from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_session
from ..db.models import Measurement, StudentDataset
from ..schemas.student import ActivityStatus, DatasetDetail, MeasurementBulkRequest, MeasurementOut
from ..services.auth import require_student
from ..services.student_data import bulk_replace_measurements, get_measurements, get_or_create_dataset

router = APIRouter()

_VALID_ACTIVITIES = frozenset({1, 2, 3, 4})
_VALID_PLAYERS = frozenset({1, 2})


def _check_activity(activity: int) -> None:
    if activity not in _VALID_ACTIVITIES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Activity must be 1–4")


def _dataset_to_detail(dataset: StudentDataset, measurements: list[Measurement]) -> DatasetDetail:
    return DatasetDetail(
        dataset_id=dataset.id,
        activity=dataset.activity,
        is_locked=dataset.is_locked,
        unlock_requested=dataset.unlock_requested,
        measurements=[
            MeasurementOut(id=m.id, player=m.player, roll_number=m.roll_number, dice_count=m.dice_count)
            for m in measurements
        ],
    )


@router.get("/activities")
async def list_activities(
    student_id: int = Depends(require_student),
    session: AsyncSession = Depends(get_session),
) -> list[ActivityStatus]:
    statuses = []
    for activity in range(1, 5):
        dataset = await get_or_create_dataset(session, student_id, activity)
        count = await session.scalar(
            select(func.count()).select_from(Measurement).where(Measurement.dataset_id == dataset.id)
        )
        statuses.append(
            ActivityStatus(
                activity=activity,
                dataset_id=dataset.id,
                is_locked=dataset.is_locked,
                unlock_requested=dataset.unlock_requested,
                measurement_count=count or 0,
            )
        )
    await session.commit()
    return statuses


@router.get("/activities/{activity}")
async def get_activity(
    activity: int,
    student_id: int = Depends(require_student),
    session: AsyncSession = Depends(get_session),
) -> DatasetDetail:
    _check_activity(activity)
    dataset = await get_or_create_dataset(session, student_id, activity)
    measurements = await get_measurements(session, dataset.id)
    await session.commit()
    return _dataset_to_detail(dataset, measurements)


@router.put("/activities/{activity}/measurements")
async def save_measurements(
    activity: int,
    body: MeasurementBulkRequest,
    student_id: int = Depends(require_student),
    session: AsyncSession = Depends(get_session),
) -> DatasetDetail:
    _check_activity(activity)
    if body.player not in _VALID_PLAYERS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Player must be 1 or 2")
    dataset = await get_or_create_dataset(session, student_id, activity)
    if dataset.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dataset is locked")
    await bulk_replace_measurements(
        session,
        dataset.id,
        body.player,
        [(r.roll_number, r.dice_count) for r in body.rows],
    )
    await session.commit()
    measurements = await get_measurements(session, dataset.id)
    return _dataset_to_detail(dataset, measurements)


@router.post("/activities/{activity}/request-unlock")
async def request_unlock(
    activity: int,
    student_id: int = Depends(require_student),
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    _check_activity(activity)
    dataset = await session.scalar(
        select(StudentDataset).where(
            StudentDataset.student_id == student_id,
            StudentDataset.activity == activity,
        )
    )
    if dataset is None or not dataset.is_locked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Dataset is not locked")
    dataset.unlock_requested = True
    await session.commit()
    return {"ok": True}
