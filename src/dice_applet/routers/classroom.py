from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.base import get_session
from ..db.models import Classroom
from ..schemas.classroom import ClassroomDetailResponse, StudentSummary
from ..services.auth import require_teacher

router = APIRouter(dependencies=[Depends(require_teacher)])


@router.get("/{classroom_id}")
async def get_classroom(
    classroom_id: int,
    session: AsyncSession = Depends(get_session),
) -> ClassroomDetailResponse:
    classroom = await session.scalar(
        select(Classroom).where(Classroom.id == classroom_id).options(selectinload(Classroom.students))
    )
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Classroom not found")

    return ClassroomDetailResponse(
        id=classroom.id,
        name=classroom.name,
        join_code=classroom.join_code,
        is_active=classroom.is_active,
        students=[
            StudentSummary(id=s.id, animal_name=s.animal_name, personal_code=s.personal_code)
            for s in classroom.students
        ],
    )
