from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.base import get_session
from ..db.models import Classroom, School, Student, TeacherSchool, TeacherSchoolStatus
from ..schemas.teacher import (
    ClassroomCreateRequest,
    ClassroomCreateResponse,
    ClassroomListItem,
    PendingSchoolRequestItem,
    SchoolItem,
)
from ..services.animals import generate_join_code
from ..services.auth import require_teacher

router = APIRouter()


@router.post("/classrooms")
async def create_classroom(
    body: ClassroomCreateRequest,
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> ClassroomCreateResponse:
    approved = await session.scalar(
        select(TeacherSchool).where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == body.school_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
    )
    if not approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not approved for this school")

    join_code = await _generate_unique_join_code(session)
    classroom = Classroom(name=body.name, join_code=join_code, school_id=body.school_id)
    session.add(classroom)
    await session.commit()
    await session.refresh(classroom)
    return ClassroomCreateResponse(id=classroom.id, name=classroom.name, join_code=classroom.join_code)


@router.get("/classrooms")
async def list_classrooms(
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> list[ClassroomListItem]:
    approved_school_ids_result = await session.execute(
        select(TeacherSchool.school_id).where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
    )
    approved_school_ids = [row[0] for row in approved_school_ids_result]

    stmt = (
        select(Classroom)
        .where(Classroom.school_id.in_(approved_school_ids))
        .options(selectinload(Classroom.students))
        .order_by(Classroom.created_at.desc())
    )
    result = await session.execute(stmt)
    return [
        ClassroomListItem(
            id=c.id,
            name=c.name,
            join_code=c.join_code,
            is_active=c.is_active,
            student_count=len(c.students),
        )
        for c in result.scalars()
    ]


@router.get("/schools")
async def list_schools(
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> list[SchoolItem]:
    """List schools where the caller is an approved teacher."""
    stmt = (
        select(School)
        .join(TeacherSchool, TeacherSchool.school_id == School.id)
        .where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
        .order_by(School.name)
    )
    result = await session.execute(stmt)
    return [SchoolItem(id=s.id, name=s.name) for s in result.scalars()]


@router.get("/pending-requests")
async def list_pending_requests(
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> list[PendingSchoolRequestItem]:
    """List pending_school requests for schools where the caller is an approved teacher."""
    approved_school_ids_result = await session.execute(
        select(TeacherSchool.school_id).where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
    )
    approved_school_ids = [row[0] for row in approved_school_ids_result]

    stmt = (
        select(TeacherSchool)
        .where(
            TeacherSchool.school_id.in_(approved_school_ids),
            TeacherSchool.status == TeacherSchoolStatus.pending_school,
        )
        .options(selectinload(TeacherSchool.teacher), selectinload(TeacherSchool.school))
        .order_by(TeacherSchool.requested_at)
    )
    result = await session.execute(stmt)
    return [
        PendingSchoolRequestItem(
            id=ts.id,
            teacher_email=ts.teacher.email,
            school_name=ts.school.name,
            requested_at=ts.requested_at.isoformat(),
        )
        for ts in result.scalars()
    ]


@router.post("/pending-requests/{teacher_school_id}/approve")
async def approve_pending_request(
    teacher_school_id: int,
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Approve a pending_school request for a school the caller manages."""
    ts = await session.get(TeacherSchool, teacher_school_id, options=[selectinload(TeacherSchool.school)])
    if not ts or ts.status != TeacherSchoolStatus.pending_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    caller_approved = await session.scalar(
        select(TeacherSchool).where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == ts.school_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
    )
    if not caller_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not approved for this school")

    ts.status = TeacherSchoolStatus.approved
    ts.resolved_by = teacher_id
    ts.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True}


@router.post("/pending-requests/{teacher_school_id}/reject")
async def reject_pending_request(
    teacher_school_id: int,
    teacher_id: int = Depends(require_teacher),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Reject a pending_school request for a school the caller manages."""
    ts = await session.get(TeacherSchool, teacher_school_id)
    if not ts or ts.status != TeacherSchoolStatus.pending_school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    caller_approved = await session.scalar(
        select(TeacherSchool).where(
            TeacherSchool.teacher_id == teacher_id,
            TeacherSchool.school_id == ts.school_id,
            TeacherSchool.status == TeacherSchoolStatus.approved,
        )
    )
    if not caller_approved:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not approved for this school")

    ts.status = TeacherSchoolStatus.rejected
    ts.resolved_by = teacher_id
    ts.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True}


async def _generate_unique_join_code(session: AsyncSession) -> str:
    """Generate a join code, retrying on the rare collision with an existing classroom."""
    while True:
        code = generate_join_code()
        existing = await session.scalar(select(Classroom).where(Classroom.join_code == code))
        if existing is None:
            return code
