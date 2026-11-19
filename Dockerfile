ARG BASE_IMAGE=ghcr.io/pytorch/pytorch:2.10.0-cuda13.0-cudnn9-runtime@sha256:c6492b180a13a2b168042969b04e56feba7d0ecbf70e96faa1689d691b63c0fe
FROM ${BASE_IMAGE}
ENV DEBIAN_FRONTEND=noninteractive PYTHONUNBUFFERED=1 COMFY_ROOT=/opt/ComfyUI MODEL_ROOT=/runpod-volume/models
RUN for source in /etc/apt/sources.list /etc/apt/sources.list.d/ubuntu.sources; do \
        if [ -f "$source" ]; then \
            sed -i -e 's|http://archive.ubuntu.com/ubuntu|https://archive.ubuntu.com/ubuntu|g' \
                   -e 's|http://security.ubuntu.com/ubuntu|https://security.ubuntu.com/ubuntu|g' "$source"; \
        fi; \
    done && \
    apt-get -o Acquire::Retries=5 update && \
    apt-get -o Acquire::Retries=5 install -y --no-install-recommends git ffmpeg libgl1 libglib2.0-0 python3-venv && \
    rm -rf /var/lib/apt/lists/*
RUN python -m venv --system-site-packages /opt/venv && \
    /opt/venv/bin/python -c "import torch; print('base torch', torch.__version__)"
ENV PATH="/opt/venv/bin:${PATH}"
ARG COMFYUI_REF=master
RUN git clone --depth 1 --branch "$COMFYUI_REF" https://github.com/Comfy-Org/ComfyUI.git /opt/ComfyUI
RUN pip install --no-cache-dir -r /opt/ComfyUI/requirements.txt
RUN python -c "import torch, comfy_kitchen; assert torch.__version__.startswith('2.10.0'), torch.__version__; assert torch.version.cuda == '13.0', torch.version.cuda; print('torch', torch.__version__, 'cuda', torch.version.cuda, 'comfy_kitchen import ok')"
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app/
RUN mkdir -p /runpod-volume/models /opt/ComfyUI/input /opt/ComfyUI/output && \
    chmod +x /app/start.sh /app/scripts/*.sh
RUN python /app/scripts/smoke_comfyui.py
ENV PYTHONPATH=/app
CMD ["/app/start.sh"]
