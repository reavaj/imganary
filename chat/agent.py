import json
from pathlib import Path

import anthropic

from .config import ChatSettings
from .system_prompt import SYSTEM_PROMPT
from .tools.image_utils import encode_image_base64, guess_media_type
from .tools.registry import ToolRegistry


class ChatAgent:
    def __init__(self, config: ChatSettings):
        self.config = config
        self.client = anthropic.Anthropic(
            api_key=config.anthropic_api_key.get_secret_value()
        )
        self.model = config.claude_model
        self.messages: list[dict] = []
        self.current_image: str | None = None
        self._image_needs_sending = False
        self.tools = ToolRegistry(config)
        self.turn_count = 0

    def set_active_image(self, path: str):
        resolved = str(Path(path).expanduser().resolve())
        if not Path(resolved).exists():
            print(f"  Warning: image not found: {resolved}")
            return
        self.current_image = resolved
        self._image_needs_sending = True
        print(f"  Active image: {resolved}")

    def run(self):
        print("imganary — AI image editing chat")
        print("Commands: /image <path>, /library, /quit")
        print()

        if self.current_image:
            print(f"Active image: {self.current_image}")
            print()

        while self.turn_count < self.config.max_turns:
            try:
                user_input = input("you: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nBye!")
                break

            if not user_input:
                continue

            if user_input in ("/quit", "/exit", "/q"):
                print("Bye!")
                break

            if user_input.startswith("/image "):
                self.set_active_image(user_input[7:].strip())
                continue

            if user_input == "/library":
                self._show_library()
                continue

            self._append_user_message(user_input)
            self._run_turn()
            self.turn_count += 1

    def _append_user_message(self, text: str):
        content = []

        # Embed active image if it hasn't been sent yet
        if self.current_image and self._image_needs_sending:
            try:
                image_data = encode_image_base64(self.current_image)
                media_type = guess_media_type(self.current_image)
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    },
                })
                self._image_needs_sending = False
            except Exception as e:
                print(f"  Warning: couldn't embed image: {e}")

        content.append({"type": "text", "text": text})
        self.messages.append({"role": "user", "content": content})

    def _run_turn(self):
        while True:
            try:
                response = self.client.messages.create(
                    model=self.model,
                    system=SYSTEM_PROMPT,
                    messages=self.messages,
                    tools=self.tools.tool_definitions(),
                    max_tokens=self.config.max_response_tokens,
                )
            except anthropic.APIError as e:
                print(f"\n  API error: {e}")
                return

            # Add assistant response to history
            self.messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Print any text blocks
            self._print_text_blocks(response.content)

            if response.stop_reason == "end_turn":
                break

            if response.stop_reason == "tool_use":
                tool_results = self._execute_tools(response.content)
                self.messages.append({
                    "role": "user",
                    "content": tool_results,
                })
                # Continue loop — Claude sees tool results

    def _print_text_blocks(self, content):
        for block in content:
            if block.type == "text":
                print(f"\nassistant: {block.text}")

    def _execute_tools(self, content) -> list[dict]:
        results = []
        for block in content:
            if block.type != "tool_use":
                continue

            print(f"\n  [tool: {block.name}]")
            result_str = self.tools.execute(block.name, block.input)

            # Track output images from GIMP execution
            if block.name == "execute_gimp_script":
                self._track_output_image(result_str)

            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })
        return results

    def _track_output_image(self, result_str: str):
        """If GIMP produced an output image, update active image."""
        try:
            result = json.loads(result_str)
            if result.get("exit_code") == 0:
                # Look for output path in stdout
                stdout = result.get("stdout", "")
                for line in stdout.splitlines():
                    if line.startswith("Saved:") or line.startswith("Output saved to:"):
                        path = line.split(":", 1)[1].strip()
                        if Path(path).exists():
                            self.current_image = path
                            self._image_needs_sending = True
                            print(f"  Active image updated: {path}")
                            return
        except (json.JSONDecodeError, KeyError):
            pass

    def _show_library(self):
        from .tools.library import handle_search_library
        result = handle_search_library(config=self.config)
        scripts = result.get("scripts", [])
        if not scripts:
            print("\n  Library is empty. Save scripts during chat!")
            return
        print(f"\n  Script library ({len(scripts)} scripts):")
        for s in scripts:
            tags = ", ".join(s.get("tags", []))
            print(f"    [{s['category']}] {s['name']} — {s['description']}")
            if tags:
                print(f"           tags: {tags}")
        print()
