from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, HTTPException, status
from jose import jwt

from ..config import settings

ALGORITHM = "HS256"
COOKIE_NAME = "dice_session"


def create_teacher_token() -> str:
    """Create a signed JWT identifying the bearer as the teacher, valid for 12 hours."""
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"role": "teacher", "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def verify_teacher_token(token: str) -> bool:
    """Return True if token is a valid, unexpired teacher session token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("role") == "teacher"
    except Exception:
        return False


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


async def require_teacher(dice_session: str | None = Cookie(default=None)) -> None:
    """FastAPI dependency that rejects requests without a valid teacher session cookie."""
    if not dice_session or not verify_teacher_token(dice_session):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
