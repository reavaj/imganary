import uuid
from pathlib import Path


def handle_generate_gimp_script(
    script_code: str,
    description: str,
    input_path: str,
    output_path: str | None = None,
) -> dict:
    # Auto-generate output path if not provided
    if not output_path:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_edited{p.suffix}")

    # Validate script
    warnings = []
    if "Gimp.quit" in script_code or "gimp.quit" in script_code:
        warnings.append(
            "Script contains Gimp.quit() — removed. "
            "The --quit flag handles exit."
        )
        script_code = script_code.replace("Gimp.quit()", "")
        script_code = script_code.replace("gimp.quit(0)", "")

    if 'gi.require_version("Gimp"' not in script_code:
        warnings.append("Script missing gi.require_version — may fail.")

    if "get_active_drawable" in script_code:
        warnings.append(
            "Script uses get_active_drawable() — "
            "GIMP 3.x requires image.get_layers()[0]"
        )

    # Write to temp file
    script_id = uuid.uuid4().hex[:8]
    temp_path = f"/tmp/imganary_{script_id}.py"
    Path(temp_path).write_text(script_code)

    result = {
        "temp_script_path": temp_path,
        "output_path": output_path,
        "status": "ready",
    }
    if warnings:
        result["warnings"] = warnings
    return result
