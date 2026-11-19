#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fixture="$(mktemp -d)"
trap 'rm -rf "$fixture"' EXIT
cp "$root/start.sh" "$fixture/start.sh"
cat > "$fixture/handler.py" <<'PY'
raise RuntimeError("simulated startup failure")
PY
echo "fake ComfyUI error clue" > "$fixture/comfyui.log"

set +e
KEEP_ALIVE_ON_STARTUP_ERROR=1 COMFY_LOG_PATH="$fixture/comfyui.log" timeout 3s bash "$fixture/start.sh" > "$fixture/output.log" 2>&1
exit_code=$?
set -e

if [[ "$exit_code" -ne 124 ]]; then
    cat "$fixture/output.log"
    echo "Expected the debug container to stay alive until timeout; got exit $exit_code" >&2
    exit 1
fi
grep -q "Keeping container alive" "$fixture/output.log"
grep -q "fake ComfyUI error clue" "$fixture/output.log"

mkdir -p "$fixture/scripts"
cat > "$fixture/scripts/download_models.sh" <<'SH'
#!/usr/bin/env bash
echo "simulated model download failure" >&2
exit 42
SH
set +e
KEEP_ALIVE_ON_STARTUP_ERROR=1 AUTO_DOWNLOAD_MODELS=1 timeout 3s bash "$fixture/start.sh" > "$fixture/download.log" 2>&1
exit_code=$?
set -e

if [[ "$exit_code" -ne 124 ]]; then
    cat "$fixture/download.log"
    echo "Expected a model download failure to keep the container alive; got exit $exit_code" >&2
    exit 1
fi
grep -q "simulated model download failure" "$fixture/download.log"
grep -q "Keeping container alive" "$fixture/download.log"
