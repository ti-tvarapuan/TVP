FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LD_LIBRARY_PATH=/usr/local/lib/python3.12/site-packages/nvidia/cublas/lib:/usr/local/lib/python3.12/site-packages/nvidia/cudnn/lib

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
COPY . .
RUN mkdir -p /app/videos

ENV VIDEO_FOLDER=/app/videos
EXPOSE 5000
CMD ["python", "main.py"]
