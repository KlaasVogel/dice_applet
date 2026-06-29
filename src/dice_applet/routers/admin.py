from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db.base import get_session
from ..db.models import School, Teacher, TeacherSchool, TeacherSchoolStatus
from ..schemas.admin import PendingRequestItem, SchoolItem, TeacherItem
from ..services.auth import require_admin

router = APIRouter(dependencies=[Depends(require_admin)])


@router.get("/requests", response_model=list[PendingRequestItem])
async def list_pending_requests(session: AsyncSession = Depends(get_session)) -> list[PendingRequestItem]:
    """List all pending teacher-school requests."""
    stmt = (
        select(TeacherSchool)
        .where(TeacherSchool.status.in_([TeacherSchoolStatus.pending_admin, TeacherSchoolStatus.pending_school]))
        .options(selectinload(TeacherSchool.teacher), selectinload(TeacherSchool.school))
        .order_by(TeacherSchool.requested_at)
    )
    result = await session.execute(stmt)
    return [
        PendingRequestItem(
            id=ts.id,
            teacher_email=ts.teacher.email,
            school_name=ts.school.name,
            status=ts.status.value,
            requested_at=ts.requested_at,
        )
        for ts in result.scalars()
    ]


@router.post("/requests/{teacher_school_id}/approve")
async def approve_request(
    teacher_school_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Approve a pending teacher-school request; activates the school if it was pending_admin."""
    ts = await session.get(TeacherSchool, teacher_school_id, options=[selectinload(TeacherSchool.school)])
    if not ts or ts.status not in (TeacherSchoolStatus.pending_admin, TeacherSchoolStatus.pending_school):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    if ts.status == TeacherSchoolStatus.pending_admin:
        ts.school.is_active = True

    ts.status = TeacherSchoolStatus.approved
    ts.resolved_by = None
    ts.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True}


@router.post("/requests/{teacher_school_id}/reject")
async def reject_request(
    teacher_school_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Reject a pending teacher-school request."""
    ts = await session.get(TeacherSchool, teacher_school_id)
    if not ts or ts.status not in (TeacherSchoolStatus.pending_admin, TeacherSchoolStatus.pending_school):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pending request not found")

    ts.status = TeacherSchoolStatus.rejected
    ts.resolved_at = datetime.now(timezone.utc)
    await session.commit()
    return {"ok": True}


@router.get("/schools", response_model=list[SchoolItem])
async def list_schools(session: AsyncSession = Depends(get_session)) -> list[SchoolItem]:
    """List all schools (active and inactive)."""
    result = await session.execute(select(School).order_by(School.name))
    return [
        SchoolItem(id=s.id, name=s.name, is_active=s.is_active, created_at=s.created_at)
        for s in result.scalars()
    ]


@router.get("/teachers", response_model=list[TeacherItem])
async def list_teachers(session: AsyncSession = Depends(get_session)) -> list[TeacherItem]:
    """List all teachers with their school links and statuses."""
    stmt = select(Teacher).options(selectinload(Teacher.school_links).selectinload(TeacherSchool.school))
    result = await session.execute(stmt)
    return [
        TeacherItem(
            id=t.id,
            email=t.email,
            created_at=t.created_at,
            schools=[
                {"school_name": link.school.name, "status": link.status.value}
                for link in t.school_links
            ],
        )
        for t in result.scalars()
    ]
