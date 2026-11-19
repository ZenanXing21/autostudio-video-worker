import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    comfy_root: Path = Path(os.getenv("COMFY_ROOT", "/opt/ComfyUI"))
    model_root: Path = Path(os.getenv("MODEL_ROOT", "/runpod-volume/models"))
    comfy_url: str = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
    work_dir: Path = Path(os.getenv("WORK_DIR", "/tmp/autostudio"))
    local_output_dir: Path = Path(os.getenv("LOCAL_OUTPUT_DIR", "/workspace/outputs"))
    job_timeout: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "1800"))
    s3_bucket: str = os.getenv("S3_BUCKET", "")
    s3_endpoint: str | None = os.getenv("S3_ENDPOINT_URL") or None
    s3_region: str = os.getenv("S3_REGION", "us-east-1")
    s3_prefix: str = os.getenv("S3_PREFIX", "videos").strip("/")
    gpu_hourly_usd: float = float(os.getenv("GPU_HOURLY_USD", "0"))


MODEL_FILES = {
    "diffusion_models": "wan2.2_ti2v_5B_fp16.safetensors",
    "text_encoders": "umt5_xxl_fp8_e4m3fn_scaled.safetensors",
    "vae": "wan2.2_vae.safetensors",
}
