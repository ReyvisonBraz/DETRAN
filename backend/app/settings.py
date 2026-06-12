"""Configuracao do backend, lida de variaveis de ambiente."""

import os

# Diretorio onde os PDFs/boletos gerados sao guardados temporariamente
STORAGE_DIR = os.getenv("STORAGE_DIR", os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "storage"
))

# Origens permitidas para o frontend (CORS). Separadas por virgula.
CORS_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

# Chave do 2Captcha (o motor tambem le TWOCAPTCHA_API_KEY)
TWOCAPTCHA_API_KEY = os.getenv("TWOCAPTCHA_API_KEY", "")

# Quantos jobs processar em paralelo (cada um consome 1 thread)
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "2"))

os.makedirs(STORAGE_DIR, exist_ok=True)
