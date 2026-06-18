"""Upload de PDFs para o Firebase Storage com URL de download por 5 dias.

Configuração no Render (variáveis de ambiente):
    FIREBASE_PROJECT_ID      → ID do projeto Firebase
    FIREBASE_CLIENT_EMAIL    → e-mail da service account
    FIREBASE_PRIVATE_KEY     → chave privada (com \\n literal ou \n real)
    FIREBASE_STORAGE_BUCKET  → ex: seu-projeto.firebasestorage.app

Se qualquer uma dessas variáveis estiver ausente, o upload é pulado
silenciosamente e a URL local (/api/documentos/...) é usada como fallback.
"""

import os
import logging
from datetime import timedelta
from typing import Optional

logger = logging.getLogger(__name__)

_app = None
_bucket = None


def _init() -> bool:
    """Inicializa o Firebase Admin SDK. Retorna True se OK."""
    global _app, _bucket

    if _bucket is not None:
        return True

    project_id    = os.getenv("FIREBASE_PROJECT_ID", "")
    client_email  = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    private_key   = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    bucket_name   = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    if not all([project_id, client_email, private_key, bucket_name]):
        logger.debug("[storage] Variáveis do Firebase não configuradas — usando storage local.")
        return False

    try:
        import firebase_admin
        from firebase_admin import credentials, storage

        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID", "key"),
            "private_key": private_key,
            "client_email": client_email,
            "client_id": "",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{client_email}",
        })

        # Só inicializa uma vez (processo Python reutiliza o app)
        try:
            _app = firebase_admin.get_app()
        except ValueError:
            _app = firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})

        _bucket = storage.bucket()
        logger.info(f"[storage] Firebase Storage inicializado — bucket: {bucket_name}")
        return True

    except Exception as e:
        logger.warning(f"[storage] Falha ao inicializar Firebase: {e}")
        return False


def upload_pdf(local_path: str, filename: str) -> Optional[str]:
    """
    Faz upload do PDF para o Firebase Storage.
    Retorna URL assinada válida por 5 dias, ou None se o upload falhar.

    O arquivo local NÃO é removido aqui — é responsabilidade do chamador.
    """
    if not _init():
        return None

    try:
        blob = _bucket.blob(f"pdfs/{filename}")
        blob.upload_from_filename(local_path, content_type="application/pdf")

        # URL assinada válida por 5 dias
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
    """Remove um PDF do Firebase Storage. Usado opcionalmente para limpeza manual."""
    if not _init():
        return False
    try:
        blob = _bucket.blob(f"pdfs/{filename}")
        blob.delete()
        return True
    except Exception:
        return False
