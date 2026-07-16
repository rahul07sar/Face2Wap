# Face2Wap Worker Dockerfile.

FROM python:3.12-slim

WORKDIR /app

ARG FACE2WAP_RUNTIME_VARIANT=gpu
ARG FACE2WAP_INSTALL_FACEFUSION=0
ARG FACEFUSION_REF=3.7.1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    git \
  && rm -rf /var/lib/apt/lists/*

COPY services/worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Local development containers do not ship with CUDA runtime libraries.
# Swap the GPU runtime package for the CPU runtime when requested by Compose.
RUN if [ "$FACE2WAP_RUNTIME_VARIANT" = "cpu" ]; then \
      pip uninstall -y onnxruntime-gpu && \
      pip install --no-cache-dir "onnxruntime>=1.23.0"; \
    fi

RUN if [ "$FACE2WAP_INSTALL_FACEFUSION" = "1" ]; then \
      git clone --depth 1 --branch "$FACEFUSION_REF" \
        https://github.com/facefusion/facefusion /opt/facefusion && \
      cd /opt/facefusion && \
      if [ "$FACE2WAP_RUNTIME_VARIANT" = "cpu" ]; then \
        python install.py default --skip-conda; \
      else \
        python install.py cuda --skip-conda; \
      fi; \
    fi

COPY services/worker/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
