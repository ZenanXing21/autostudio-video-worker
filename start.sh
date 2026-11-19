#!/usr/bin/env bash
set -euo pipefail
if [[ "${AUTO_DOWNLOAD_MODELS:-0}" == "1" ]]; then
    bash /app/scripts/download_models.sh
fi
exec python /app/handler.py
