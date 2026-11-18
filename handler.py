import logging
import os
import re
import time
import uuid

import runpod

from app.comfyui_manager import ComfyUI
from app.config import Settings
from app.gpu_manager import GPU_LOCK, check_gpu
from app.storage import ObjectStorage
from app.validators import InputError, parse_request
from app.workflow_engine import build_prompt, validate_graph


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
settings = Settings()
comfy = ComfyUI(settings)
storage = None


def initialize() -> None:
    global storage
    log.info("GPU: %s", check_gpu())
    comfy.ensure_models()
    storage = ObjectStorage(settings)
    comfy.start()
    for mode in ("t2v", "i2v"):
        from pathlib import Path
        import json
        graph = json.loads((Path(__file__).parent / "workflows" / f"wan22_{mode}.api.json").read_text())
        validate_graph(graph, comfy.nodes())


def handler(job: dict) -> dict:
    started = time.monotonic()
    raw_id = str(job.get("id") or uuid.uuid4().hex)
    task_id = re.sub(r"[^A-Za-z0-9_-]", "_", raw_id)[:80]
    try:
        request = parse_request(job.get("input", {}))
        if storage is None:
            raise RuntimeError("Worker initialization failed")
        if not GPU_LOCK.acquire(blocking=False):
            return {"status": "failed", "task_id": task_id, "error": "GPU worker is busy; retry job"}
        try:
            if storage.existing(task_id):
                return {"status": "completed", "task_id": task_id, "video_url": storage.url(task_id),
                        "duration": request.duration, "resolution": request.resolution,
                        "generation_time": 0, "cached": True, "estimated_gpu_cost_usd": 0}
            if not comfy.ready():
                comfy.start()
            image_name = None
            if request.mode == "i2v":
                data = request.image_bytes or comfy.download_image(request.image_url)
                image_name = comfy.upload_image(data, task_id)
            graph = build_prompt(request, image_name, task_id)
            validate_graph(graph, comfy.nodes())
            path = comfy.execute(graph, task_id, settings.job_timeout)
            url = storage.upload(path, task_id)
            elapsed = round(time.monotonic() - started, 2)
            return {"status": "completed", "task_id": task_id, "video_url": url,
                    "duration": request.duration, "resolution": request.resolution,
                    "generation_time": elapsed,
                    "estimated_gpu_cost_usd": round(elapsed / 3600 * settings.gpu_hourly_usd, 6)}
        finally:
            GPU_LOCK.release()
    except Exception as exc:
        log.exception("Video job failed: %s", task_id)
        message = str(exc)
        if "out of memory" in message.lower():
            message = "GPU out of memory; retry with resolution=480p or shorter duration"
        return {"status": "failed", "task_id": task_id, "error": message[:1200],
                "generation_time": round(time.monotonic() - started, 2)}


if __name__ == "__main__":
    initialize()
    runpod.serverless.start({"handler": handler})
