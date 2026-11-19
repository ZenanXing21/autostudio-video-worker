import logging
import subprocess
import threading


GPU_LOCK = threading.Lock()
log = logging.getLogger(__name__)


class GPUError(RuntimeError):
    pass


def check_gpu() -> dict:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    lines = result.stdout.strip().splitlines()
    if not lines:
        raise GPUError("nvidia-smi returned no GPU data")
    first = lines[0].rsplit(",", 1)
    if len(first) != 2 or not first[0].strip():
        raise GPUError(f"Cannot parse nvidia-smi GPU data: {lines[0]!r}")
    memory_text = first[1].strip()
    try:
        memory_mib = int(memory_text)
    except ValueError:
        memory_mib = None
        log.warning("GPU memory unavailable from nvidia-smi (%s); skipping startup memory threshold", memory_text)
    if memory_mib is not None and memory_mib < 22_000:
        raise GPUError(f"At least 22,000 MiB GPU memory is required; found {memory_mib} MiB")
    return {"name": first[0].strip(), "memory_mib": memory_mib}
