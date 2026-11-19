"""Fail the image build unless ComfyUI's CPU-mode HTTP API starts."""

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


def main() -> None:
    comfy_root = Path(os.environ.get("COMFY_ROOT", "/opt/ComfyUI"))
    command = [sys.executable, "main.py", "--cpu", "--listen", "127.0.0.1",
               "--port", "8199", "--disable-auto-launch"]
    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as output:
        process = subprocess.Popen(command, cwd=comfy_root, stdout=output,
                                   stderr=subprocess.STDOUT)
        try:
            deadline = time.monotonic() + 90
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"ComfyUI exited with code {process.returncode}")
                try:
                    with urlopen("http://127.0.0.1:8199/system_stats", timeout=2) as response:
                        if response.status == 200:
                            print("ComfyUI CPU startup smoke test passed")
                            return
                except (OSError, URLError):
                    pass
                time.sleep(1)
            raise TimeoutError("ComfyUI CPU API did not become ready in 90 seconds")
        except Exception:
            output.seek(0)
            print("Last ComfyUI startup log lines:\n" + "".join(output.readlines()[-100:]),
                  file=sys.stderr)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


if __name__ == "__main__":
    main()
