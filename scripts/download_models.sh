#!/usr/bin/env bash
set -euo pipefail
MODEL_ROOT="${MODEL_ROOT:-/runpod-volume/models}"
mkdir -p "$MODEL_ROOT"/{diffusion_models,text_encoders,vae}
hf download Comfy-Org/Wan_2.2_ComfyUI_Repackaged split_files/diffusion_models/wan2.2_ti2v_5B_fp16.safetensors --local-dir "$MODEL_ROOT"
hf download Comfy-Org/Wan_2.2_ComfyUI_Repackaged split_files/vae/wan2.2_vae.safetensors --local-dir "$MODEL_ROOT"
hf download Comfy-Org/Wan_2.1_ComfyUI_repackaged split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors --local-dir "$MODEL_ROOT"
for category in diffusion_models vae text_encoders; do
  mv "$MODEL_ROOT/split_files/$category/"* "$MODEL_ROOT/$category/"
done
