from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.base import get_session
from ..db.models import School, Teacher, TeacherSchool, TeacherSchoolStatus
from ..schemas.auth import LoginRequest, MeResponse, RegisterRequest
from ..services.auth import (
    COOKIE_NAME,
    create_admin_token,
    create_teacher_token,
    hash_password,
    require_admin_or_teacher,
    verify_password,
)

router = APIRouter()

_ALLOWED_EMAIL_DOMAIN = "@carmelhengelo.nl"


@router.post("/login")
async def login(
    body: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Unified login for admin (no email) and teachers (email + password)."""
    if not body.email:
        if not verify_password(body.password, settings.teacher_password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")
        token = create_admin_token()
    else:
        teacher = await session.scalar(select(Teacher).where(Teacher.email == body.email))
        if not teacher or not verify_password(body.password, teacher.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        has_approved = await session.scalar(
            select(TeacherSchool).where(
                TeacherSchool.teacher_id == teacher.id,
                TeacherSchool.status == TeacherSchoolStatus.approved,
            )
        )
        if not has_approved:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account pending approval")
        token = create_teacher_token(teacher.id)

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=12 * 3600,
    )
    return {"ok": True}


@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register(
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Teacher self-registration; creates a pending TeacherSchool link."""
    if not body.email.lower().endswith(_ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only @carmelhengelo.nl addresses are accepted")

    if bool(body.school_id) == bool(body.new_school_name):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provide exactly one of school_id or new_school_name")

    existing = await session.scalar(select(Teacher).where(Teacher.email == body.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    teacher = Teacher(email=body.email, password_hash=hash_password(body.password))
    session.add(teacher)
    await session.flush()

    if body.new_school_name:
        school = School(name=body.new_school_name, is_active=False)
        session.add(school)
        await session.flush()
        link = TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.pending_admin)
    else:
        school = await session.get(School, body.school_id)
        if not school or not school.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
        link = TeacherSchool(teacher_id=teacher.id, school_id=school.id, status=TeacherSchoolStatus.pending_school)

    session.add(link)
    await session.commit()
    return {"ok": True, "pending": True}


@router.post("/logout")
async def logout(response: Response) -> dict[str, bool]:
    """Clear the session cookie."""
    response.delete_cookie(key=COOKIE_NAME)
    return {"ok": True}


@router.get("/me", response_model=MeResponse)
async def me(
    session: AsyncSession = Depends(get_session),
    payload: dict = Depends(require_admin_or_teacher),
) -> MeResponse:
    """Return the current session's identity, or 401 if not logged in."""
    role = payload["role"]
    if role == "admin":
        return MeResponse(role="admin")
    teacher_id = payload["teacher_id"]
    teacher = await session.get(Teacher, teacher_id)
    if not teacher:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return MeResponse(role="teacher", teacher_id=teacher.id, email=teacher.email)
