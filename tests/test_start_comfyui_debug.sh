#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
cat > "$fixture/main.py" <<'PY'
import sys

print("fake ComfyUI stdout")
print("fake ComfyUI stderr", file=sys.stderr)
sys.exit(17)
PY

log_path="$fixture/logs/comfyui.log"
set +e
COMFY_ROOT="$fixture" MODEL_ROOT="$fixture/models" AUTO_DOWNLOAD_MODELS=1 COMFY_LOG_PATH="$log_path" bash "$root/scripts/start_comfyui.sh" > "$fixture/console.log" 2>&1
exit_code=$?
set -e

if [[ "$exit_code" -ne 17 ]]; then
    cat "$fixture/console.log"
    echo "Expected fake ComfyUI exit 17; got $exit_code" >&2
    exit 1
fi
grep -q "fake ComfyUI stdout" "$log_path"
grep -q "fake ComfyUI stderr" "$log_path"
grep -Fq "MODEL_ROOT=$fixture/models" "$log_path"
grep -q "AUTO_DOWNLOAD_MODELS=1" "$log_path"
grep -q "ComfyUI command: python main.py" "$log_path"
