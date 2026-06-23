from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..db.base import get_session
from ..db.models import Classroom, Student
from ..schemas.teacher import ClassroomCreateRequest, ClassroomCreateResponse, ClassroomListItem, TeacherLoginRequest
from ..services.animals import generate_join_code
from ..services.auth import COOKIE_NAME, create_teacher_token, require_teacher, verify_password

router = APIRouter()


@router.post("/login")
async def login(body: TeacherLoginRequest, response: Response) -> dict[str, bool]:
    if not verify_password(body.password, settings.teacher_password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password")

    token = create_teacher_token()
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=12 * 3600,
    )
    return {"ok": True}


@router.delete("/logout")
async def logout(response: Response) -> dict[str, bool]:
    response.delete_cookie(key=COOKIE_NAME)
    return {"ok": True}


@router.post("/classrooms", dependencies=[Depends(require_teacher)])
async def create_classroom(
    body: ClassroomCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> ClassroomCreateResponse:
    join_code = await _generate_unique_join_code(session)
    classroom = Classroom(name=body.name, join_code=join_code)
    session.add(classroom)
    await session.commit()
    await session.refresh(classroom)
    return ClassroomCreateResponse(id=classroom.id, name=classroom.name, join_code=classroom.join_code)


@router.get("/classrooms", dependencies=[Depends(require_teacher)])
async def list_classrooms(session: AsyncSession = Depends(get_session)) -> list[ClassroomListItem]:
    stmt = (
        select(Classroom, func.count(Student.id))
        .outerjoin(Student, Student.classroom_id == Classroom.id)
        .group_by(Classroom.id)
        .order_by(Classroom.created_at.desc())
    )
    result = await session.execute(stmt)
    return [
        ClassroomListItem(
            id=classroom.id,
            name=classroom.name,
            join_code=classroom.join_code,
            is_active=classroom.is_active,
            student_count=student_count,
        )
        for classroom, student_count in result.all()
    ]


async def _generate_unique_join_code(session: AsyncSession) -> str:
    """Generate a join code, retrying on the rare collision with an existing classroom."""
    while True:
        code = generate_join_code()
        existing = await session.scalar(select(Classroom).where(Classroom.join_code == code))
        if existing is None:
            return code
