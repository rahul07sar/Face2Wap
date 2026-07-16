# Face2Wap Worker Dockerfile.

FROM python:3.12-slim

WORKDIR /app

ARG FACE2WAP_RUNTIME_VARIANT=gpu

RUN apt-get update \
  && apt-get install -y --no-install-recommends ffmpeg git \
  && rm -rf /var/lib/apt/lists/*

COPY services/worker/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Local development containers do not ship with CUDA runtime libraries.
# Swap the GPU runtime package for the CPU runtime when requested by Compose.
RUN if [ "$FACE2WAP_RUNTIME_VARIANT" = "cpu" ]; then \
      pip uninstall -y onnxruntime-gpu && \
      pip install --no-cache-dir "onnxruntime>=1.23.0"; \
    fi

COPY services/worker/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
