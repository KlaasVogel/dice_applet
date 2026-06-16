import random

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Classroom, Student
from ..schemas.student import (
    StudentJoinRequest,
    StudentJoinResponse,
    StudentReconnectRequest,
    StudentReconnectResponse,
)
from ..services.animals import ANIMAL_NAMES, generate_personal_code

router = APIRouter()


@router.post("/join")
async def join(
    body: StudentJoinRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> StudentJoinResponse:
    classroom = await session.scalar(
        select(Classroom).where(Classroom.join_code == body.classroom_code.strip().upper())
    )
    if classroom is None or not classroom.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    client_ip = request.client.host if request.client else None
    existing_students = (await session.scalars(select(Student).where(Student.classroom_id == classroom.id))).all()

    used_names = {s.animal_name for s in existing_students}
    available_names = [n for n in ANIMAL_NAMES if n not in used_names]
    if not available_names:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Classroom is full")
    animal_name = random.choice(available_names)
    personal_code = await _generate_unique_personal_code(session)

    student = Student(
        classroom_id=classroom.id,
        animal_name=animal_name,
        personal_code=personal_code,
        ip_address=client_ip,
    )
    session.add(student)
    await session.commit()

    known_student = next((s for s in existing_students if client_ip and s.ip_address == client_ip), None)

    return StudentJoinResponse(
        animal_name=animal_name,
        personal_code=personal_code,
        suggested_name=known_student.animal_name if known_student else None,
        suggested_code=known_student.personal_code if known_student else None,
    )


@router.post("/reconnect")
async def reconnect(
    body: StudentReconnectRequest,
    session: AsyncSession = Depends(get_session),
) -> StudentReconnectResponse:
    student = await session.scalar(select(Student).where(Student.personal_code == body.personal_code.strip().upper()))
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personal code not found")
    return StudentReconnectResponse(animal_name=student.animal_name, classroom_id=student.classroom_id)


async def _generate_unique_personal_code(session: AsyncSession) -> str:
    """Generate a personal code, retrying on the rare collision with an existing student."""
    while True:
        code = generate_personal_code()
        existing = await session.scalar(select(Student).where(Student.personal_code == code))
        if existing is None:
            return code
