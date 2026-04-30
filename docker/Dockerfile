FROM python:3.12-slim

ARG CUDA_VERSION=12.4
ARG HARDWARE_ACCELERATOR=cuda

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    VSR_DATA_DIR=/data \
    VSR_FFMPEG_PATH=/usr/bin/ffmpeg \
    PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && \
    apt-get install -y --no-install-recommends \
        ffmpeg \
        libglib2.0-0 \
        libgomp1 \
        libgl1 \
        libsm6 \
        libxext6 \
        libxrender1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /vsr

COPY requirements-api.txt requirements-runtime.txt ./

RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    python -m pip install --upgrade pip setuptools wheel && \
    pip install -r requirements-api.txt && \
    pip install paddlepaddle==3.0.0 && \
    if [ "${HARDWARE_ACCELERATOR}" = "cuda" ]; then \
        pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cu$(echo ${CUDA_VERSION} | tr -d .); \
    else \
        pip install torch==2.6.0 torchvision==0.21.0 --index-url https://download.pytorch.org/whl/cpu; \
    fi && \
    pip install -r requirements-runtime.txt

COPY . .

RUN mkdir -p /data/uploads /data/outputs

EXPOSE 8332

CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8332"]
