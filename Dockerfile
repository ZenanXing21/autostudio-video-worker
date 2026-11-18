FROM pytorch/pytorch:2.6.0-cuda12.4-cudnn9-runtime
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 COMFY_ROOT=/opt/ComfyUI MODEL_ROOT=/runpod-volume/models
RUN apt-get update && apt-get install -y --no-install-recommends git ffmpeg libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
ARG COMFYUI_REF=master
RUN git clone --depth 1 --branch "$COMFYUI_REF" https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI
RUN pip install --no-cache-dir -r /opt/ComfyUI/requirements.txt
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
RUN mkdir -p /runpod-volume/models /opt/ComfyUI/input /opt/ComfyUI/output && \
    chmod +x /app/start.sh /app/scripts/*.sh
ENV PYTHONPATH=/app
CMD ["/app/start.sh"]
