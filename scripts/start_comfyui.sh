#!/usr/bin/env bash
set -euo pipefail
cd "${COMFY_ROOT:-/opt/ComfyUI}"
exec python main.py --listen 127.0.0.1 --port 8188 --lowvram --reserve-vram 1.0 --disable-auto-launch --extra-model-paths-config /app/extra_model_paths.yaml
