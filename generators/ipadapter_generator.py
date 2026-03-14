"""Standalone FLUX IP-Adapter generator — style transfer without ComfyUI server.

Uses diffusers FluxPipeline with InstantX IP-Adapter weights and SigLIP vision
encoder. Runs entirely in-process on MPS (Apple Silicon).
"""

import logging
import random
import time
from pathlib import Path
from typing import Optional

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from .config import GeneratorSettings
from .exceptions import ImageGenerationError, InvalidPromptError
from .interfaces import GenerationResult, GeneratorType, ImageGenerator

from models.logging import get_logger


class MLPProjModel(nn.Module):
    """MLP projection: SigLIP pooler_output (1152-d) → IP-Adapter tokens (128 × 4096-d)."""

    def __init__(self, cross_attention_dim=4096, id_embeddings_dim=1152, num_tokens=128):
        super().__init__()
        self.cross_attention_dim = cross_attention_dim
        self.num_tokens = num_tokens
        self.proj = nn.Sequential(
            nn.Linear(id_embeddings_dim, id_embeddings_dim * 2),
            nn.GELU(),
            nn.Linear(id_embeddings_dim * 2, cross_attention_dim * num_tokens),
        )
        self.norm = nn.LayerNorm(cross_attention_dim)

    def forward(self, id_embeds):
        x = self.proj(id_embeds)
        x = x.reshape(-1, self.num_tokens, self.cross_attention_dim)
        x = self.norm(x)
        return x


class FluxIPAdapterDoubleAttnProcessor(nn.Module):
    """IP-Adapter attention processor for FLUX double-stream blocks.

    Returns 2 values (not 3) so the block's gate_msa applies to the combined
    attention + IP attention output — matching ComfyUI's gated approach.
    diffusers' built-in returns 3 values, adding IP attention UNGATED after
    the MLP, which causes blocky artifacts with InstantX weights.
    """

    def __init__(self, hidden_size, cross_attention_dim, num_tokens=128, scale=1.0,
                 device=None, dtype=None):
        super().__init__()
        self.hidden_size = hidden_size
        self.cross_attention_dim = cross_attention_dim
        self.scale = [scale]
        head_dim = 128  # FLUX head_dim = 3072 / 24 heads
        self.to_k_ip = nn.ModuleList([
            nn.Linear(cross_attention_dim, hidden_size, bias=False, device=device, dtype=dtype)
        ])
        self.to_v_ip = nn.ModuleList([
            nn.Linear(cross_attention_dim, hidden_size, bias=False, device=device, dtype=dtype)
        ])
        self.norm_ip_k = nn.RMSNorm(head_dim, eps=1e-5, elementwise_affine=False)
        self.norm_ip_v = nn.RMSNorm(head_dim, eps=1e-5, elementwise_affine=False)

    def __call__(
        self,
        attn,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor = None,
        attention_mask: torch.Tensor | None = None,
        image_rotary_emb: torch.Tensor | None = None,
        ip_hidden_states: list[torch.Tensor] | None = None,
    ) -> torch.Tensor:
        from diffusers.models.transformers.transformer_flux import (
            _get_qkv_projections, apply_rotary_emb, dispatch_attention_fn,
        )

        batch_size = hidden_states.shape[0]

        query, key, value, encoder_query, encoder_key, encoder_value = _get_qkv_projections(
            attn, hidden_states, encoder_hidden_states
        )

        query = query.unflatten(-1, (attn.heads, -1))
        key = key.unflatten(-1, (attn.heads, -1))
        value = value.unflatten(-1, (attn.heads, -1))

        query = attn.norm_q(query)
        key = attn.norm_k(key)
        ip_query = query  # Save pre-concat query for IP cross-attention

        if encoder_hidden_states is not None:
            encoder_query = encoder_query.unflatten(-1, (attn.heads, -1))
            encoder_key = encoder_key.unflatten(-1, (attn.heads, -1))
            encoder_value = encoder_value.unflatten(-1, (attn.heads, -1))

            encoder_query = attn.norm_added_q(encoder_query)
            encoder_key = attn.norm_added_k(encoder_key)

            query = torch.cat([encoder_query, query], dim=1)
            key = torch.cat([encoder_key, key], dim=1)
            value = torch.cat([encoder_value, value], dim=1)

        if image_rotary_emb is not None:
            query = apply_rotary_emb(query, image_rotary_emb, sequence_dim=1)
            key = apply_rotary_emb(key, image_rotary_emb, sequence_dim=1)

        hidden_states = dispatch_attention_fn(
            query, key, value,
            attn_mask=attention_mask,
            dropout_p=0.0,
            is_causal=False,
        )
        hidden_states = hidden_states.flatten(2, 3)
        hidden_states = hidden_states.to(query.dtype)

        if encoder_hidden_states is not None:
            encoder_hidden_states, hidden_states = hidden_states.split_with_sizes(
                [encoder_hidden_states.shape[1],
                 hidden_states.shape[1] - encoder_hidden_states.shape[1]], dim=1
            )
            hidden_states = attn.to_out[0](hidden_states)
            hidden_states = attn.to_out[1](hidden_states)
            encoder_hidden_states = attn.to_add_out(encoder_hidden_states)

            # IP-Adapter cross-attention with RMSNorm — added to hidden_states
            # BEFORE returning, so the block's gate_msa gates it (matching ComfyUI)
            if ip_hidden_states is not None:
                for current_ip_hidden_states, scale, to_k_ip, to_v_ip in zip(
                    ip_hidden_states, self.scale, self.to_k_ip, self.to_v_ip
                ):
                    ip_key = to_k_ip(current_ip_hidden_states)
                    ip_value = to_v_ip(current_ip_hidden_states)

                    ip_key = ip_key.view(batch_size, -1, attn.heads, attn.head_dim)
                    ip_value = ip_value.view(batch_size, -1, attn.heads, attn.head_dim)

                    ip_key = self.norm_ip_k(ip_key)
                    ip_value = self.norm_ip_v(ip_value)

                    ip_attn = dispatch_attention_fn(
                        ip_query, ip_key, ip_value,
                        attn_mask=None, dropout_p=0.0, is_causal=False,
                    )
                    ip_attn = ip_attn.reshape(batch_size, -1, attn.heads * attn.head_dim)
                    ip_attn = ip_attn.to(ip_query.dtype)
                    hidden_states = hidden_states + scale * ip_attn

            # Return 2 values — block applies gate_msa to hidden_states (incl. IP)
            return hidden_states, encoder_hidden_states
        else:
            return hidden_states


class FluxIPAdapterSingleAttnProcessor(nn.Module):
    """IP-Adapter attention processor for FLUX single-stream blocks.

    Single blocks concatenate text+image before attention and return one tensor,
    so IP attention must be added directly inside the processor output.
    Includes RMSNorm on IP key/value to match ComfyUI's implementation.
    """

    def __init__(self, hidden_size, cross_attention_dim, num_tokens=128, scale=1.0,
                 device=None, dtype=None):
        super().__init__()
        self.hidden_size = hidden_size
        self.cross_attention_dim = cross_attention_dim
        self.scale = [scale]
        head_dim = 128  # FLUX head_dim = 3072 / 24 heads
        self.to_k_ip = nn.ModuleList([
            nn.Linear(cross_attention_dim, hidden_size, bias=False, device=device, dtype=dtype)
        ])
        self.to_v_ip = nn.ModuleList([
            nn.Linear(cross_attention_dim, hidden_size, bias=False, device=device, dtype=dtype)
        ])
        self.norm_ip_k = nn.RMSNorm(head_dim, eps=1e-5, elementwise_affine=False)
        self.norm_ip_v = nn.RMSNorm(head_dim, eps=1e-5, elementwise_affine=False)

    def __call__(
        self,
        attn,
        hidden_states: torch.Tensor,
        encoder_hidden_states: torch.Tensor = None,
        attention_mask: torch.Tensor | None = None,
        image_rotary_emb: torch.Tensor | None = None,
        ip_hidden_states: list[torch.Tensor] | None = None,
    ) -> torch.Tensor:
        from diffusers.models.transformers.transformer_flux import (
            _get_qkv_projections, apply_rotary_emb, dispatch_attention_fn,
        )

        # Standard single-stream attention (encoder_hidden_states is None here)
        query, key, value, _, _, _ = _get_qkv_projections(
            attn, hidden_states, encoder_hidden_states
        )

        query = query.unflatten(-1, (attn.heads, -1))
        key = key.unflatten(-1, (attn.heads, -1))
        value = value.unflatten(-1, (attn.heads, -1))

        query = attn.norm_q(query)
        key = attn.norm_k(key)

        if image_rotary_emb is not None:
            query = apply_rotary_emb(query, image_rotary_emb, sequence_dim=1)
            key = apply_rotary_emb(key, image_rotary_emb, sequence_dim=1)

        hidden_states = dispatch_attention_fn(
            query, key, value,
            attn_mask=attention_mask,
            dropout_p=0.0,
            is_causal=False,
        )
        hidden_states = hidden_states.flatten(2, 3)
        hidden_states = hidden_states.to(query.dtype)

        # IP-Adapter cross-attention with RMSNorm (matching ComfyUI)
        if ip_hidden_states is not None:
            for current_ip_hidden_states, scale, to_k_ip, to_v_ip in zip(
                ip_hidden_states, self.scale, self.to_k_ip, self.to_v_ip
            ):
                ip_key = to_k_ip(current_ip_hidden_states)
                ip_value = to_v_ip(current_ip_hidden_states)

                ip_key = ip_key.view(-1, current_ip_hidden_states.shape[-2],
                                     attn.heads, attn.head_dim)
                ip_value = ip_value.view(-1, current_ip_hidden_states.shape[-2],
                                         attn.heads, attn.head_dim)

                # RMSNorm per-head (the key difference from previous version)
                ip_key = self.norm_ip_k(ip_key)
                ip_value = self.norm_ip_v(ip_value)

                ip_attn = dispatch_attention_fn(
                    query, ip_key, ip_value,
                    attn_mask=None, dropout_p=0.0, is_causal=False,
                )
                ip_attn = ip_attn.flatten(2, 3).to(query.dtype)
                hidden_states = hidden_states + scale * ip_attn

        return hidden_states


class IPAdapterGenerator(ImageGenerator):
    """Standalone FLUX IP-Adapter using diffusers + SigLIP (no server needed)."""

    def __init__(self, generator_type: GeneratorType, settings: GeneratorSettings):
        self._type = generator_type
        self._settings = settings
        self._logger = get_logger("imganary.ipadapter", settings.log_level)
        self._pipe = None
        self._pipe_is_img2img = False
        self._image_encoder = None
        self._image_proj = None

    @property
    def generator_type(self) -> GeneratorType:
        return self._type

    def _ip_adapter_weights_path(self) -> str:
        """Resolve IP-Adapter weights path (auto-downloads ~5.3GB on first use)."""
        from huggingface_hub import hf_hub_download
        return hf_hub_download(
            repo_id="InstantX/FLUX.1-dev-IP-Adapter",
            filename="ip-adapter.bin",
        )

    def _load_pipeline(self, need_img2img: bool = False):
        """Lazy-load the FLUX pipeline, SigLIP encoder, and IP-Adapter weights."""
        # If we already have the right pipeline type, reuse it
        if self._pipe is not None:
            if need_img2img == self._pipe_is_img2img:
                return
            # Wrong pipeline type — need to reload
            self._logger.info(
                f"Switching pipeline: {'img2img' if need_img2img else 'txt2img'}"
            )
            self._pipe = None

        from diffusers import FluxPipeline, FluxImg2ImgPipeline
        PipelineClass = FluxImg2ImgPipeline if need_img2img else FluxPipeline
        from diffusers.models.embeddings import MultiIPAdapterImageProjection
        from transformers import SiglipVisionModel, SiglipImageProcessor

        device = "mps"
        dtype = torch.bfloat16  # FLUX needs bfloat16's wider dynamic range; fp16 overflows in attention

        # 1. Load FLUX pipeline
        self._logger.info(
            "Loading FLUX.1-dev pipeline via diffusers (first run downloads ~24GB)..."
        )
        pipe = PipelineClass.from_pretrained(
            "black-forest-labs/FLUX.1-dev",
            torch_dtype=dtype,
        )
        pipe.to(device)

        # 2. Load SigLIP vision encoder (suppress "UNEXPECTED key" warnings —
        #    the checkpoint contains text+vision weights but we only load vision)
        self._logger.info("Loading SigLIP vision encoder...")
        import transformers.modeling_utils
        _orig_level = transformers.modeling_utils.logger.level
        transformers.modeling_utils.logger.setLevel(logging.ERROR)
        self._image_encoder = (
            SiglipVisionModel.from_pretrained("google/siglip-so400m-patch14-384")
            .to(device, dtype=dtype)
            .eval()
        )
        transformers.modeling_utils.logger.setLevel(_orig_level)
        self._clip_processor = SiglipImageProcessor.from_pretrained(
            "google/siglip-so400m-patch14-384"
        )

        # 3. Load IP-Adapter weights
        self._logger.info("Loading IP-Adapter weights...")
        ip_ckpt = self._ip_adapter_weights_path()
        state_dict = torch.load(ip_ckpt, map_location="cpu", weights_only=True)

        # 4. MLP projection model
        self._image_proj = MLPProjModel(
            cross_attention_dim=4096,
            id_embeddings_dim=1152,
            num_tokens=128,
        ).to(device, dtype=dtype)
        self._image_proj.load_state_dict(state_dict["image_proj"], strict=True)

        # Wire MLP into pipeline's transformer
        pipe.transformer.encoder_hid_proj = MultiIPAdapterImageProjection(
            [self._image_proj]
        )
        pipe.transformer.config.encoder_hid_dim_type = "ip_image_proj"

        # 5. Set IP-Adapter attention processors on ALL blocks (57 total)
        # InstantX weights: 0-18 = double blocks, 19-56 = single blocks
        attn_procs = {}
        key_id = 0
        for name in pipe.transformer.attn_processors.keys():
            if name.startswith("single_transformer_blocks"):
                # Single blocks: custom processor (adds IP attention inline)
                proc = FluxIPAdapterSingleAttnProcessor(
                    hidden_size=pipe.transformer.inner_dim,
                    cross_attention_dim=pipe.transformer.config.joint_attention_dim,
                    num_tokens=128,
                    scale=1.0,
                    device=device,
                    dtype=dtype,
                )
                weight_dict = {
                    "to_k_ip.0.weight": state_dict["ip_adapter"][f"{key_id}.to_k_ip.weight"],
                    "to_v_ip.0.weight": state_dict["ip_adapter"][f"{key_id}.to_v_ip.weight"],
                }
                proc.load_state_dict(weight_dict, strict=False)
                attn_procs[name] = proc
                key_id += 1
            else:
                # Double blocks: custom processor — returns 2 values so gate_msa
                # applies to IP attention (matching ComfyUI's gated approach)
                proc = FluxIPAdapterDoubleAttnProcessor(
                    hidden_size=pipe.transformer.inner_dim,
                    cross_attention_dim=pipe.transformer.config.joint_attention_dim,
                    num_tokens=128,
                    scale=1.0,
                    device=device,
                    dtype=dtype,
                )
                weight_dict = {
                    "to_k_ip.0.weight": state_dict["ip_adapter"][f"{key_id}.to_k_ip.weight"],
                    "to_v_ip.0.weight": state_dict["ip_adapter"][f"{key_id}.to_v_ip.weight"],
                }
                proc.load_state_dict(weight_dict, strict=False)
                attn_procs[name] = proc
                key_id += 1

        pipe.transformer.set_attn_processor(attn_procs)
        self._logger.info(f"Loaded IP-Adapter on {key_id} blocks (19 double + 38 single)")
        del state_dict

        self._pipe = pipe
        self._pipe_is_img2img = need_img2img
        self._logger.info("IP-Adapter pipeline ready")

    @torch.inference_mode()
    def _encode_style_image(self, pil_image: Image.Image) -> torch.Tensor:
        """Encode a single style reference image via SigLIP → pooler_output."""
        clip_input = self._clip_processor(
            images=[pil_image], return_tensors="pt"
        ).pixel_values
        pooler_output = self._image_encoder(
            clip_input.to(self._image_encoder.device, dtype=self._image_encoder.dtype)
        ).pooler_output  # (1, 1152)
        return pooler_output  # (1, 1152)

    def _encode_style_images(
        self, *pil_images: Image.Image
    ) -> list[torch.Tensor]:
        """Encode one or more style reference images and concatenate embeddings.

        Each image is encoded separately via SigLIP, then concatenated along the
        image dimension. The MLP projects each 1152-d embedding into 128 IP tokens,
        so 2 images → 256 tokens the attention layers attend to.
        """
        embeddings = [self._encode_style_image(img) for img in pil_images]
        # Stack along image dim: (1, N, 1152) where N = number of images
        combined = torch.cat(embeddings, dim=0).unsqueeze(0)  # (1, N, 1152)
        return [combined]

    def _set_scale(self, scale: float):
        """Update IP-Adapter influence scale on all processors."""
        for proc in self._pipe.transformer.attn_processors.values():
            if hasattr(proc, "scale"):
                proc.scale = [scale]

    def generate(
        self,
        prompt: str,
        output_path: str | Path,
        width: int = 1024,
        height: int = 1024,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
        image_path: Optional[str | Path] = None,
        image_strength: Optional[float] = None,
        guidance: Optional[float] = None,
        controlnet_image_path: Optional[str | Path] = None,
        controlnet_strength: Optional[float] = None,
        base_image_path: Optional[str | Path] = None,
        base_image_strength: Optional[float] = None,
    ) -> GenerationResult:
        if not prompt or not prompt.strip():
            raise InvalidPromptError("Prompt cannot be empty")

        output_path = Path(output_path).expanduser()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        steps = steps or 25
        seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        guidance = guidance if guidance is not None else self._settings.flux_guidance
        style_strength = image_strength if image_strength is not None else 0.7

        self._load_pipeline(need_img2img=base_image_path is not None)

        start = time.monotonic()
        try:
            gen_kwargs = dict(
                prompt=prompt,
                width=width,
                height=height,
                num_inference_steps=steps,
                guidance_scale=guidance,
                generator=torch.Generator("mps").manual_seed(seed),
            )

            if image_path is not None:
                pil_image = Image.open(Path(image_path).expanduser()).convert("RGB")

                # Check for second style image (passed via controlnet_image_path)
                if controlnet_image_path is not None:
                    pil_image2 = Image.open(
                        Path(controlnet_image_path).expanduser()
                    ).convert("RGB")
                    image_embeds = self._encode_style_images(pil_image, pil_image2)
                    self._logger.info(
                        f"Generating with dual IP-Adapter (strength={style_strength})"
                    )
                else:
                    image_embeds = self._encode_style_images(pil_image)
                    self._logger.info(
                        f"Generating with IP-Adapter (strength={style_strength})"
                    )

                neg_embeds = [torch.zeros_like(image_embeds[0])]

                self._set_scale(style_strength)
                gen_kwargs["ip_adapter_image_embeds"] = image_embeds
                gen_kwargs["negative_ip_adapter_image_embeds"] = neg_embeds
            else:
                # IP-Adapter processors are always installed — provide zero embeddings
                # so they don't crash on None. scale=0 means no style influence.
                device = self._pipe.device
                dtype = next(self._pipe.transformer.parameters()).dtype
                zero_embeds = [torch.zeros(1, 1, 1152, device=device, dtype=dtype)]
                self._set_scale(0.0)
                gen_kwargs["ip_adapter_image_embeds"] = zero_embeds
                gen_kwargs["negative_ip_adapter_image_embeds"] = zero_embeds

                self._logger.info("Generating txt2img (no style image)")

            # img2img: use base image as starting latent (orthogonal to IP-Adapter)
            if base_image_path is not None:
                pil_base = Image.open(
                    Path(base_image_path).expanduser()
                ).convert("RGB").resize((width, height))
                gen_kwargs["image"] = pil_base
                gen_kwargs["strength"] = base_image_strength if base_image_strength is not None else 0.5
                self._logger.info(
                    f"img2img base: {base_image_path} (strength={gen_kwargs['strength']})"
                )

            result = self._pipe(**gen_kwargs)
            result.images[0].save(output_path)

        except Exception as exc:
            elapsed_ms = (time.monotonic() - start) * 1000
            return GenerationResult(
                generator_type=self._type,
                prompt=prompt,
                output_path=str(output_path),
                width=width,
                height=height,
                steps=steps,
                seed=seed,
                processing_time_ms=elapsed_ms,
                error=str(exc),
            )

        elapsed_ms = (time.monotonic() - start) * 1000
        self._logger.info(f"Generated {width}x{height} image in {elapsed_ms:.0f}ms")

        return GenerationResult(
            generator_type=self._type,
            prompt=prompt,
            output_path=str(output_path),
            width=width,
            height=height,
            steps=steps,
            seed=seed,
            processing_time_ms=elapsed_ms,
        )
