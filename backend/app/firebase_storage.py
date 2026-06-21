import os
import logging
from datetime import timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_bucket = None


def _init() -> bool:
    global _bucket

    if _bucket is not None:
        return True

    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "")
    if not bucket_name:
        logger.debug("[storage] FIREBASE_STORAGE_BUCKET nao configurado — usando storage local.")
        return False

    try:
        from app.firebase_admin import init_firebase
        app = init_firebase()

        from firebase_admin import storage
        _bucket = storage.bucket(app=app)
        logger.info(f"[storage] Firebase Storage inicializado — bucket: {bucket_name}")
        return True

    except Exception as e:
        logger.warning(f"[storage] Falha ao inicializar Firebase Storage: {e}")
        return False


def upload_pdf(local_path: str, filename: str) -> Optional[str]:
    if not _init():
        return None

    try:
        blob = _bucket.blob(f"pdfs/{filename}")
        blob.upload_from_filename(local_path, content_type="application/pdf")

        url = blob.generate_signed_url(
            expiration=timedelta(days=5),
            method="GET",
            version="v4",
        )
        logger.info(f"[storage] PDF enviado: {filename}")
        return url

    except Exception as e:
        logger.warning(f"[storage] Upload falhou para {filename}: {e}")
        return None


def deletar_pdf(filename: str) -> bool:
    if not _init():
        return False
    try:
        blob = _bucket.blob(f"pdfs/{filename}")
        blob.delete()
        return True
    except Exception:
        return False