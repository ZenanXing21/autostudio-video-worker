#!/usr/bin/env bash
set -euo pipefail
extra_model_paths_config="$(mktemp /tmp/autostudio-model-paths.XXXXXX.yaml)"
python -m app.model_paths "$extra_model_paths_config"
cd "${COMFY_ROOT:-/opt/ComfyUI}"
exec python main.py --listen 127.0.0.1 --port 8188 --lowvram --reserve-vram 1.0 --disable-auto-launch --extra-model-paths-config "$extra_model_paths_config"
