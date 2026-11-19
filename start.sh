#!/usr/bin/env bash
set -euo pipefail
script_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

keep_alive_on_error() {
    local exit_code=$?
    trap - ERR
    echo "Worker startup failed with exit code ${exit_code}. Keeping container alive for debugging." >&2
    local comfy_log="${COMFY_LOG_PATH:-/workspace/logs/comfyui.log}"
    if [[ -f "$comfy_log" ]]; then
        echo "Last 80 lines of ${comfy_log}:" >&2
        tail -n 80 "$comfy_log" >&2
    else
        echo "ComfyUI log not created yet: ${comfy_log}" >&2
    fi
    sleep infinity
}

if [[ "${KEEP_ALIVE_ON_STARTUP_ERROR:-0}" == "1" ]]; then
    trap keep_alive_on_error ERR
fi
if [[ "${AUTO_DOWNLOAD_MODELS:-0}" == "1" ]]; then
    bash "$script_root/scripts/download_models.sh"
fi
if [[ "${KEEP_ALIVE_ON_STARTUP_ERROR:-0}" == "1" ]]; then
    python "$script_root/handler.py"
else
    exec python "$script_root/handler.py"
fi
