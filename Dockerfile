# Lightweight Python 3.11 Linux base image
FROM python:3.11-slim

# System dependencies aur FFmpeg install karein
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg curl && \
    rm -rf /var/lib/apt/lists/*

# Working directory set karein
WORKDIR /app

# Dependencies copy karke install karein
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/requirements.txt

# Baaki project code copy karein (backend + frontend)
COPY backend /app/backend
COPY frontend /app/frontend

# Temporary downloads folder banayein
RUN mkdir -p /app/backend/downloads

# Environment variables
ENV PORT=5000
ENV PYTHONUNBUFFERED=1

WORKDIR /app/backend

# Gunicorn production server ke sath start karein
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "180", "app:app"]