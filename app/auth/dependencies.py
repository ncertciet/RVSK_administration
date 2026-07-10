import requests
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import jwt_handler
from app.config.settings import get_settings
from app.utils.logger import logger

settings = get_settings()

security = HTTPBearer()


def verify_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    # Verify JWT signature before calling the auth service.
    jwt_handler.verify_token(token)

    try:
        response = requests.get(
            f"{settings.AUTH_BASE_URL}/me",
            headers={
                "Authorization": f"Bearer {token}"
            },
            timeout=settings.AUTH_TIMEOUT_SECONDS
        )
    except requests.RequestException as ex:
        logger.exception(ex)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service unavailable."
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Token"
        )

    try:
        body = response.json()
    except ValueError as ex:
        logger.exception(ex)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned an invalid response."
        )

    user = body.get("data")

    if not body.get("success") or not isinstance(user, dict):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication Failed"
        )

    if not user.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive User"
        )

    if "state_id" not in user or "username" not in user:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service returned incomplete user details."
        )

    return user
