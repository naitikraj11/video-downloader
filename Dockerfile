FROM python:3.11-slim

# System tools, FFmpeg aur Git install karein
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app/backend
COPY frontend /app/frontend

RUN mkdir -p /app/backend/downloads

ENV PORT=5000
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "180", "app:app"]