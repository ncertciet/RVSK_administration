from pathlib import Path
import jwt
from fastapi import HTTPException
from app.config.settings import get_settings
settings = get_settings()


class JWTHandler:

    def __init__(self):

        key_path = Path(settings.PUBLIC_KEY_FILE)

        if not key_path.exists():
            raise RuntimeError(
                f"Public key file not found: {settings.PUBLIC_KEY_FILE}"
            )

        with open(key_path, "r", encoding="utf-8") as f:
            self.public_key = f.read()

    def verify_token(self, token: str):

        try:

            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[settings.JWT_ALGORITHM]
            )

            return payload

        except jwt.ExpiredSignatureError:

            raise HTTPException(
                status_code=401,
                detail="Access token expired."
            )

        except jwt.InvalidSignatureError:

            raise HTTPException(
                status_code=401,
                detail="Invalid JWT signature."
            )

        except jwt.InvalidTokenError:

            raise HTTPException(
                status_code=401,
                detail="Invalid access token."
            )


jwt_handler = JWTHandler()