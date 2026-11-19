#!/usr/bin/env bash
set -euo pipefail
log_path="${COMFY_LOG_PATH:-/workspace/logs/comfyui.log}"
mkdir -p "$(dirname "$log_path")"
exec >>"$log_path" 2>&1
printf '\n=== ComfyUI launch ===\n'
printf 'MODEL_ROOT=%s\n' "${MODEL_ROOT:-/runpod-volume/models}"
printf 'AUTO_DOWNLOAD_MODELS=%s\n' "${AUTO_DOWNLOAD_MODELS:-0}"
printf 'COMFY_ROOT=%s\n' "${COMFY_ROOT:-/opt/ComfyUI}"
extra_model_paths_config="$(mktemp /tmp/autostudio-model-paths.XXXXXX.yaml)"
python -m app.model_paths "$extra_model_paths_config"
cd "${COMFY_ROOT:-/opt/ComfyUI}"
command=(python main.py --listen 127.0.0.1 --port 8188 --lowvram --reserve-vram 1.0 --disable-auto-launch --extra-model-paths-config "$extra_model_paths_config")
printf 'ComfyUI command:'
printf ' %q' "${command[@]}"
printf '\n'
exec "${command[@]}"
