from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import Measurement, StudentDataset


async def get_or_create_dataset(session: AsyncSession, student_id: int, activity: int) -> StudentDataset:
    """Return the StudentDataset for this student+activity, creating it if absent."""
    dataset = await session.scalar(
        select(StudentDataset).where(
            StudentDataset.student_id == student_id,
            StudentDataset.activity == activity,
        )
    )
    if dataset is None:
        dataset = StudentDataset(student_id=student_id, activity=activity)
        session.add(dataset)
        await session.flush()
    return dataset


async def get_measurements(session: AsyncSession, dataset_id: int) -> list[Measurement]:
    """Return all measurements for a dataset, ordered by player then roll number."""
    result = await session.scalars(
        select(Measurement)
        .where(Measurement.dataset_id == dataset_id)
        .order_by(Measurement.player, Measurement.roll_number)
    )
    return list(result.all())


async def bulk_replace_measurements(
    session: AsyncSession,
    dataset_id: int,
    player: int,
    rows: list[tuple[int, int]],
) -> None:
    """Delete all existing measurements for (dataset, player) and insert the new rows."""
    await session.execute(
        delete(Measurement).where(
            Measurement.dataset_id == dataset_id,
            Measurement.player == player,
        )
    )
    for roll_number, dice_count in rows:
        session.add(Measurement(dataset_id=dataset_id, player=player, roll_number=roll_number, dice_count=dice_count))
