import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> dict:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticacao ausente.",
        )

    token = credentials.credentials
    try:
        from firebase_admin import auth as firebase_auth
        from app.firebase_admin import get_app

        app = get_app()
        decoded = firebase_auth.verify_id_token(token, app=app)
        return {
            "uid": decoded["uid"],
            "email": decoded.get("email", ""),
            "email_verified": decoded.get("email_verified", False),
        }
    except Exception as e:
        logger.warning(f"Token invalido: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido ou expirado.",
        )