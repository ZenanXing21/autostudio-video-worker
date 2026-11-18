import io
import subprocess
import time
from pathlib import Path

import requests
from PIL import Image

from .config import MODEL_FILES, Settings


class ComfyError(RuntimeError):
    pass


class ComfyUI:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.session = requests.Session()
        self.process = None

    def ensure_models(self) -> None:
        missing = [str(self.settings.model_root / folder / name)
                   for folder, name in MODEL_FILES.items()
                   if not (self.settings.model_root / folder / name).is_file()]
        if missing:
            raise ComfyError("Missing model files: " + ", ".join(missing))

    def ready(self) -> bool:
        try:
            return self.session.get(f"{self.settings.comfy_url}/system_stats", timeout=3).ok
        except requests.RequestException:
            return False

    def start(self) -> None:
        if not self.ready():
            self.process = subprocess.Popen(["bash", "/app/scripts/start_comfyui.sh"],
                                            stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            if self.ready():
                return
            if self.process and self.process.poll() is not None:
                raise ComfyError(f"ComfyUI exited with code {self.process.returncode}")
            time.sleep(2)
        raise ComfyError("ComfyUI API did not become ready in 180 seconds")

    def nodes(self) -> set[str]:
        response = self.session.get(f"{self.settings.comfy_url}/object_info", timeout=30)
        response.raise_for_status()
        return set(response.json())

    def upload_image(self, data: bytes, task_id: str) -> str:
        if len(data) > 20 * 1024 * 1024:
            raise ComfyError("Image exceeds 20 MiB")
        try:
            image = Image.open(io.BytesIO(data))
            image.verify()
        except Exception as exc:
            raise ComfyError("Image is invalid") from exc
        # Normalize every supported input format to PNG before the Comfy upload.
        image = Image.open(io.BytesIO(data)).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        name = f"{task_id}.png"
        response = self.session.post(f"{self.settings.comfy_url}/upload/image",
                                     files={"image": (name, buffer.getvalue(), "image/png")},
                                     data={"overwrite": "true"}, timeout=60)
        response.raise_for_status()
        return response.json()["name"]

    def download_image(self, url: str) -> bytes:
        # Host resolution is checked again by the validator before each request.
        from .validators import public_https_url
        public_https_url(url)
        with self.session.get(url, stream=True, allow_redirects=False, timeout=(10, 30)) as response:
            response.raise_for_status()
            data = bytearray()
            for chunk in response.iter_content(1024 * 1024):
                data.extend(chunk)
                if len(data) > 20 * 1024 * 1024:
                    raise ComfyError("Downloaded image exceeds 20 MiB")
        return bytes(data)

    def execute(self, graph: dict, task_id: str, timeout: int) -> Path:
        response = self.session.post(f"{self.settings.comfy_url}/prompt",
                                     json={"prompt": graph, "client_id": task_id}, timeout=30)
        if not response.ok:
            raise ComfyError(f"ComfyUI rejected workflow: {response.text[:1000]}")
        prompt_id = response.json()["prompt_id"]
        deadline = time.monotonic() + timeout
        try:
            while time.monotonic() < deadline:
                history_response = self.session.get(f"{self.settings.comfy_url}/history/{prompt_id}", timeout=30)
                history_response.raise_for_status()
                history = history_response.json().get(prompt_id)
                if history:
                    status = history.get("status", {})
                    if status.get("status_str") == "error" or status.get("completed") is False:
                        raise ComfyError(f"ComfyUI execution failed: {status.get('messages', [])!s}"[:1200])
                    if status.get("completed"):
                        output = history.get("outputs", {}).get("58", {})
                        videos = [item for key in ("images", "gifs", "videos")
                                  for item in output.get(key, [])
                                  if item.get("filename", "").endswith(".mp4")]
                        if not videos:
                            raise ComfyError("SaveVideo completed without video output metadata")
                        item = videos[0]
                        if item.get("type") != "output" or not item.get("filename", "").endswith(".mp4"):
                            raise ComfyError("SaveVideo output is not an MP4")
                        output_root = (self.settings.comfy_root / "output").resolve()
                        path = (output_root / item.get("subfolder", "") / item["filename"]).resolve()
                        if not path.is_relative_to(output_root):
                            raise ComfyError("Unsafe ComfyUI output path")
                        return path
                time.sleep(2)
            raise ComfyError(f"ComfyUI timed out after {timeout} seconds")
        except Exception:
            try:
                self.session.post(f"{self.settings.comfy_url}/interrupt", timeout=5)
            finally:
                raise
