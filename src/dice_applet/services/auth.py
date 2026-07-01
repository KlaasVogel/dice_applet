from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt

from ..config import settings

ALGORITHM = "HS256"
COOKIE_NAME = "dice_session"
STUDENT_COOKIE_NAME = "student_session"


def create_admin_token() -> str:
    """Create a signed JWT for the admin (.env-hash) role, valid for 12 hours."""
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode({"role": "admin", "exp": expire}, settings.secret_key, algorithm=ALGORITHM)


def create_teacher_token(teacher_id: int) -> str:
    """Create a signed JWT for a DB-backed teacher, valid for 12 hours."""
    expire = datetime.now(timezone.utc) + timedelta(hours=12)
    return jwt.encode(
        {"role": "teacher", "teacher_id": teacher_id, "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def verify_password(plain: str, hashed: str) -> bool:
    """Check a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _decode_token(token: str) -> dict:
    """Decode and return JWT payload, raising 401 on any error."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


async def require_admin(dice_session: str | None = Cookie(default=None)) -> None:
    """FastAPI dependency: rejects requests without a valid admin session cookie."""
    if not dice_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = _decode_token(dice_session)
    if payload.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


async def require_teacher(dice_session: str | None = Cookie(default=None)) -> int:
    """FastAPI dependency: rejects requests without a valid teacher session; returns teacher_id."""
    if not dice_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = _decode_token(dice_session)
    if payload.get("role") != "teacher":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    teacher_id = payload.get("teacher_id")
    if not isinstance(teacher_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return teacher_id


def create_student_token(student_id: int) -> str:
    """Create a signed JWT for a student, valid for 24 hours."""
    expire = datetime.now(timezone.utc) + timedelta(hours=24)
    return jwt.encode(
        {"role": "student", "student_id": student_id, "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


async def require_student(student_session: str | None = Cookie(default=None)) -> int:
    """FastAPI dependency: rejects requests without a valid student session; returns student_id."""
    if not student_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = _decode_token(student_session)
    if payload.get("role") != "student":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    student_id = payload.get("student_id")
    if not isinstance(student_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return student_id


async def require_admin_or_teacher(dice_session: str | None = Cookie(default=None)) -> dict:
    """FastAPI dependency: accepts admin or teacher session; returns payload dict."""
    if not dice_session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    payload = _decode_token(dice_session)
    if payload.get("role") not in ("admin", "teacher"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    return payload
