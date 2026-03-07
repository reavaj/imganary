import os
import subprocess

from ..config import ChatSettings


def handle_execute_gimp_script(
    script_path: str,
    config: ChatSettings,
) -> dict:
    gimprc = os.path.expanduser(config.gimp_gimprc_path)
    cmd = [
        config.gimp_console_path,
        "-n", "-i", "--no-data", "--quit",
        f"--gimprc={gimprc}",
        "--batch-interpreter=python-fu-eval",
        "-b", f"exec(open('{script_path}').read())",
    ]
    env = {**os.environ, "LSBackgroundOnly": "1"}

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120, env=env
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {
            "exit_code": -1,
            "stdout": "",
            "stderr": "GIMP execution timed out after 120 seconds.",
        }
