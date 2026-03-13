"""Thin HTTP client for the ComfyUI REST API."""

import time
import uuid
from pathlib import Path
from typing import Optional

import httpx

from .exceptions import GenerationTimeoutError, ImageGenerationError


class ComfyUIClient:
    """Synchronous client for ComfyUI's HTTP API."""

    def __init__(self, base_url: str = "http://127.0.0.1:8188", timeout: int = 300):
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._http = httpx.Client(base_url=self._base_url, timeout=30.0)

    def ping(self) -> bool:
        """Check if the ComfyUI server is reachable."""
        try:
            resp = self._http.get("/system_stats")
            return resp.status_code == 200
        except httpx.ConnectError:
            return False

    def upload_image(self, local_path: str | Path) -> str:
        """Upload an image to ComfyUI's input directory. Returns the server filename."""
        path = Path(local_path).expanduser().resolve()
        if not path.exists():
            raise ImageGenerationError(f"Image not found: {path}")

        with open(path, "rb") as f:
            resp = self._http.post(
                "/upload/image",
                files={"image": (path.name, f, "image/png")},
                data={"overwrite": "true"},
            )
        if resp.status_code != 200:
            raise ImageGenerationError(f"Image upload failed: {resp.text}")

        data = resp.json()
        return data["name"]

    def queue_prompt(self, workflow: dict) -> str:
        """Submit a workflow to the queue. Returns the prompt_id."""
        client_id = str(uuid.uuid4())
        payload = {"prompt": workflow, "client_id": client_id}

        try:
            resp = self._http.post("/prompt", json=payload)
        except httpx.ConnectError:
            raise ImageGenerationError(
                f"ComfyUI server not reachable at {self._base_url}"
            )

        data = resp.json()
        if data.get("error"):
            node_errors = data.get("node_errors", {})
            msg = f"Workflow error: {data['error']}"
            if node_errors:
                details = "; ".join(
                    f"node {nid}: {err}" for nid, err in node_errors.items()
                )
                msg += f" ({details})"
            raise ImageGenerationError(msg)

        return data["prompt_id"]

    def wait_for_result(self, prompt_id: str) -> dict:
        """Poll /history until the prompt completes. Returns the output dict."""
        deadline = time.monotonic() + self._timeout
        poll_interval = 2.0

        while time.monotonic() < deadline:
            resp = self._http.get(f"/history/{prompt_id}")
            if resp.status_code == 200:
                history = resp.json()
                if prompt_id in history:
                    return history[prompt_id]
            time.sleep(poll_interval)

        raise GenerationTimeoutError(
            f"ComfyUI generation timed out after {self._timeout}s"
        )

    def download_image(
        self,
        filename: str,
        output_path: str | Path,
        subfolder: str = "",
        image_type: str = "output",
    ) -> Path:
        """Download a generated image from ComfyUI to a local path."""
        out = Path(output_path).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)

        resp = self._http.get(
            "/view",
            params={"filename": filename, "subfolder": subfolder, "type": image_type},
        )
        if resp.status_code != 200:
            raise ImageGenerationError(
                f"Failed to download image '{filename}': HTTP {resp.status_code}"
            )

        out.write_bytes(resp.content)
        return out

    def find_output_images(self, result: dict) -> list[dict]:
        """Extract image info dicts from a history result."""
        images = []
        outputs = result.get("outputs", {})
        for node_output in outputs.values():
            if "images" in node_output:
                images.extend(node_output["images"])
        return images
