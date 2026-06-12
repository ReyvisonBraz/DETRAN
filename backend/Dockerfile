# Backend desacoplado de plataforma: roda igual em Render, Fly.io, Koyeb,
# Oracle Cloud ou qualquer VPS com Docker.
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencias de sistema para lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev \
    && rm -rf /var/lib/apt/lists/* || true

# Instala dependencias primeiro (cache de camada)
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copia o motor existente e o backend
COPY detran-pa-consultas /app/detran-pa-consultas
COPY backend /app/backend

WORKDIR /app/backend

EXPOSE 8000

# $PORT e injetado por Render/Fly/etc; cai para 8000 localmente
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
