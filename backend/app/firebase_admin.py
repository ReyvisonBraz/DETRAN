import os
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)

_app = None


def init_firebase():
    global _app
    if _app is not None:
        return _app

    project_id = os.getenv("FIREBASE_PROJECT_ID", "")
    client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "")
    private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").replace("\\n", "\n")
    bucket_name = os.getenv("FIREBASE_STORAGE_BUCKET", "")

    if not all([project_id, client_email, private_key]):
        raise RuntimeError(
            "Firebase Admin nao configurado. Defina FIREBASE_PROJECT_ID, "
            "FIREBASE_CLIENT_EMAIL e FIREBASE_PRIVATE_KEY."
        )

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

    options = {}
    if bucket_name:
        options["storageBucket"] = bucket_name

    try:
        _app = firebase_admin.get_app()
    except ValueError:
        _app = firebase_admin.initialize_app(cred, options)

    logger.info("[firebase] Firebase Admin SDK inicializado")
    return _app


def get_app():
    if _app is None:
        return init_firebase()
    return _app