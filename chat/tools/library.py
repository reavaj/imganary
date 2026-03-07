import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from ..config import ChatSettings


class ScriptParameter(BaseModel):
    name: str
    type: str  # "str", "float", "int", "bool"
    default: Any
    description: str


class LibraryEntry(BaseModel):
    name: str
    category: str
    path: str
    description: str
    parameters: list[ScriptParameter] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ScriptLibrary(BaseModel):
    version: int = 1
    scripts: list[LibraryEntry] = Field(default_factory=list)


def _load_index(config: ChatSettings) -> ScriptLibrary:
    index_path = config.scripts_dir / "_index.json"
    if index_path.exists():
        data = json.loads(index_path.read_text())
        return ScriptLibrary.model_validate(data)
    return ScriptLibrary()


def _save_index(config: ChatSettings, library: ScriptLibrary):
    index_path = config.scripts_dir / "_index.json"
    index_path.write_text(
        library.model_dump_json(indent=2) + "\n"
    )


def handle_save_to_library(
    name: str,
    category: str,
    description: str,
    script_code: str,
    tags: list[str] | None = None,
    parameters: list[dict] | None = None,
    config: ChatSettings | None = None,
) -> dict:
    scripts_dir = config.scripts_dir
    category_dir = scripts_dir / category
    category_dir.mkdir(parents=True, exist_ok=True)

    # Write script file
    script_path = category_dir / f"{name}.py"
    script_path.write_text(script_code)

    # Build library entry
    params = []
    if parameters:
        params = [ScriptParameter(**p) for p in parameters]

    entry = LibraryEntry(
        name=name,
        category=category,
        path=str(script_path.relative_to(scripts_dir.parent)),
        description=description,
        parameters=params,
        tags=tags or [],
    )

    # Update index
    library = _load_index(config)
    # Replace if exists
    library.scripts = [s for s in library.scripts if s.name != name]
    library.scripts.append(entry)
    _save_index(config, library)

    return {
        "saved_to": str(script_path),
        "entry": entry.model_dump(mode="json"),
    }


def handle_search_library(
    query: str | None = None,
    category: str | None = None,
    config: ChatSettings | None = None,
) -> dict:
    library = _load_index(config)
    results = library.scripts

    if category:
        results = [s for s in results if s.category == category]

    if query:
        q = query.lower()
        results = [
            s for s in results
            if q in s.name.lower()
            or q in s.description.lower()
            or any(q in t.lower() for t in s.tags)
        ]

    return {
        "count": len(results),
        "scripts": [s.model_dump(mode="json") for s in results],
    }


def handle_load_library_script(
    script_name: str,
    input_path: str,
    output_path: str | None = None,
    parameters: dict | None = None,
    config: ChatSettings | None = None,
) -> dict:
    library = _load_index(config)
    entry = next((s for s in library.scripts if s.name == script_name), None)
    if not entry:
        return {"error": f"Script '{script_name}' not found in library."}

    # Read template
    script_file = config.project_root / entry.path
    if not script_file.exists():
        return {"error": f"Script file missing: {script_file}"}
    template = script_file.read_text()

    # Auto-generate output path if not provided
    if not output_path:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_{script_name}{p.suffix}")

    # Inject parameters
    code = template.replace("__INPUT_PATH__", input_path)
    code = code.replace("__OUTPUT_PATH__", output_path)
    if parameters:
        for param_name, value in parameters.items():
            placeholder = f"__{param_name.upper()}__"
            if isinstance(value, str):
                code = code.replace(placeholder, f'"{value}"')
            else:
                code = code.replace(placeholder, str(value))

    # Write to temp file
    script_id = uuid.uuid4().hex[:8]
    temp_path = f"/tmp/imganary_{script_id}.py"
    Path(temp_path).write_text(code)

    return {
        "temp_script_path": temp_path,
        "output_path": output_path,
        "status": "ready",
        "script_name": script_name,
        "description": entry.description,
    }
