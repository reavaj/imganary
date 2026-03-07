import json
from typing import Any, Callable

from ..config import ChatSettings
from .analyze_image import handle_analyze_image
from .execute_gimp import handle_execute_gimp_script
from .generate_script import handle_generate_gimp_script
from .image_utils import get_image_info
from .library import (
    handle_load_library_script,
    handle_save_to_library,
    handle_search_library,
)

# Claude API tool definitions
TOOL_DEFINITIONS = [
    {
        "name": "get_image_info",
        "description": (
            "Get basic image metadata: dimensions, format, color mode, "
            "file size. Fast, no model needed."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Absolute path to the image file.",
                },
            },
            "required": ["image_path"],
        },
    },
    {
        "name": "analyze_image",
        "description": (
            "Run a vision model on an image. "
            "LLaVA: free-text scene description. "
            "YOLO: object detection with bounding boxes. "
            "CLIP: semantic label matching."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "image_path": {
                    "type": "string",
                    "description": "Absolute path to the image file.",
                },
                "model": {
                    "type": "string",
                    "enum": ["llava", "yolo", "clip"],
                    "description": "Which vision model to use.",
                },
            },
            "required": ["image_path", "model"],
        },
    },
    {
        "name": "generate_gimp_script",
        "description": (
            "Validate and prepare a GIMP 3.x Python-Fu script for "
            "execution. Writes the script to a temp file and returns "
            "the path. Call execute_gimp_script next to run it."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script_code": {
                    "type": "string",
                    "description": (
                        "The full GIMP 3.x Python-Fu script code."
                    ),
                },
                "description": {
                    "type": "string",
                    "description": "Brief description of what the script does.",
                },
                "input_path": {
                    "type": "string",
                    "description": "Absolute path to the input image.",
                },
                "output_path": {
                    "type": "string",
                    "description": (
                        "Absolute path for the output image. "
                        "Auto-generated if omitted."
                    ),
                },
            },
            "required": ["script_code", "description", "input_path"],
        },
    },
    {
        "name": "execute_gimp_script",
        "description": (
            "Execute a prepared GIMP Python-Fu script via gimp-console "
            "batch mode. Use generate_gimp_script first to create the "
            "temp script file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script_path": {
                    "type": "string",
                    "description": (
                        "Path to the temp script file "
                        "(from generate_gimp_script)."
                    ),
                },
            },
            "required": ["script_path"],
        },
    },
    {
        "name": "save_to_library",
        "description": (
            "Save a working GIMP script to the reusable library. "
            "Replace hardcoded values with __PLACEHOLDER__ names "
            "so the script can be reused with different parameters."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": (
                        "Script name (snake_case, e.g. 'warm_tint')."
                    ),
                },
                "category": {
                    "type": "string",
                    "enum": ["color", "transform", "filters", "compositing"],
                    "description": "Script category.",
                },
                "description": {
                    "type": "string",
                    "description": "What the script does.",
                },
                "script_code": {
                    "type": "string",
                    "description": (
                        "The parameterized script with __PLACEHOLDER__ "
                        "variables for reusable values."
                    ),
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Searchable tags.",
                },
                "parameters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "type": {"type": "string"},
                            "default": {},
                            "description": {"type": "string"},
                        },
                        "required": ["name", "type", "default", "description"],
                    },
                    "description": (
                        "List of configurable parameters "
                        "(excluding INPUT_PATH/OUTPUT_PATH)."
                    ),
                },
            },
            "required": [
                "name", "category", "description", "script_code", "tags",
            ],
        },
    },
    {
        "name": "search_library",
        "description": (
            "Search the script library by name, description, or tags."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search term to match against name, "
                        "description, and tags."
                    ),
                },
                "category": {
                    "type": "string",
                    "enum": ["color", "transform", "filters", "compositing"],
                    "description": "Filter by category.",
                },
            },
        },
    },
    {
        "name": "load_library_script",
        "description": (
            "Load a saved script from the library, inject new parameter "
            "values, and prepare it for execution."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "script_name": {
                    "type": "string",
                    "description": "Name of the library script to load.",
                },
                "input_path": {
                    "type": "string",
                    "description": "Absolute path to the input image.",
                },
                "output_path": {
                    "type": "string",
                    "description": (
                        "Absolute path for output. Auto-generated if omitted."
                    ),
                },
                "parameters": {
                    "type": "object",
                    "description": (
                        "Parameter values to inject "
                        "(e.g. {\"WARMTH\": 0.5})."
                    ),
                },
            },
            "required": ["script_name", "input_path"],
        },
    },
]


class ToolRegistry:
    def __init__(self, config: ChatSettings):
        self._config = config

    def tool_definitions(self) -> list[dict]:
        return TOOL_DEFINITIONS

    def execute(self, tool_name: str, tool_input: dict) -> str:
        handlers: dict[str, Callable] = {
            "get_image_info": self._handle_image_info,
            "analyze_image": self._handle_analyze,
            "generate_gimp_script": self._handle_generate,
            "execute_gimp_script": self._handle_execute,
            "save_to_library": self._handle_save,
            "search_library": self._handle_search,
            "load_library_script": self._handle_load,
        }
        handler = handlers.get(tool_name)
        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})
        try:
            result = handler(tool_input)
            return json.dumps(result, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _handle_image_info(self, inp: dict) -> dict:
        return get_image_info(inp["image_path"])

    def _handle_analyze(self, inp: dict) -> dict:
        return handle_analyze_image(inp["image_path"], inp["model"])

    def _handle_generate(self, inp: dict) -> dict:
        return handle_generate_gimp_script(
            script_code=inp["script_code"],
            description=inp["description"],
            input_path=inp["input_path"],
            output_path=inp.get("output_path"),
        )

    def _handle_execute(self, inp: dict) -> dict:
        return handle_execute_gimp_script(
            script_path=inp["script_path"],
            config=self._config,
        )

    def _handle_save(self, inp: dict) -> dict:
        return handle_save_to_library(
            name=inp["name"],
            category=inp["category"],
            description=inp["description"],
            script_code=inp["script_code"],
            tags=inp.get("tags"),
            parameters=inp.get("parameters"),
            config=self._config,
        )

    def _handle_search(self, inp: dict) -> dict:
        return handle_search_library(
            query=inp.get("query"),
            category=inp.get("category"),
            config=self._config,
        )

    def _handle_load(self, inp: dict) -> dict:
        return handle_load_library_script(
            script_name=inp["script_name"],
            input_path=inp["input_path"],
            output_path=inp.get("output_path"),
            parameters=inp.get("parameters"),
            config=self._config,
        )
