#!/usr/bin/env bash
set -euo pipefail
MODEL_ROOT="${MODEL_ROOT:-/runpod-volume/models}"
mkdir -p "$MODEL_ROOT"/{diffusion_models,text_encoders,vae}

download_model() {
  local repository="$1" category="$2" filename="$3"
  local destination="$MODEL_ROOT/$category/$filename"
  if [[ -s "$destination" ]]; then
    return
  fi
  local source="split_files/$category/$filename"
  hf download "$repository" "$source" --local-dir "$MODEL_ROOT"
  mv "$MODEL_ROOT/$source" "$destination"
  test -s "$destination"
}

download_model Comfy-Org/Wan_2.2_ComfyUI_Repackaged diffusion_models wan2.2_ti2v_5B_fp16.safetensors
download_model Comfy-Org/Wan_2.2_ComfyUI_Repackaged vae wan2.2_vae.safetensors
download_model Comfy-Org/Wan_2.1_ComfyUI_repackaged text_encoders umt5_xxl_fp8_e4m3fn_scaled.safetensors
