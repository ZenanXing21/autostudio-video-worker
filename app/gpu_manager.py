import subprocess
import threading


GPU_LOCK = threading.Lock()


class GPUError(RuntimeError):
    pass


def check_gpu() -> dict:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True, text=True, timeout=15, check=True,
    )
    first = result.stdout.strip().splitlines()[0].rsplit(",", 1)
    memory_mib = int(first[1].strip())
    if memory_mib < 22_000:
        raise GPUError(f"At least 22,000 MiB GPU memory is required; found {memory_mib} MiB")
    return {"name": first[0].strip(), "memory_mib": memory_mib}
