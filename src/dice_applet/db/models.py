from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Classroom(Base):
    """A teacher-managed group that students join via a code."""

    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    join_code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    students: Mapped[list["Student"]] = relationship(back_populates="classroom")


class Student(Base):
    """A student's identity within a classroom (animal name + personal code)."""

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    classroom_id: Mapped[int] = mapped_column(ForeignKey("classrooms.id"))
    animal_name: Mapped[str] = mapped_column(String(50))
    personal_code: Mapped[str] = mapped_column(String(8), unique=True, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    classroom: Mapped["Classroom"] = relationship(back_populates="students")
    datasets: Mapped[list["StudentDataset"]] = relationship(back_populates="student")


class StudentDataset(Base):
    """One row per student per activity (max 4 rows per student)."""

    __tablename__ = "student_datasets"
    __table_args__ = (UniqueConstraint("student_id", "activity", name="uq_student_activity"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"))
    activity: Mapped[int] = mapped_column(SmallInteger)
    is_locked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    unlock_requested: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")

    student: Mapped["Student"] = relationship(back_populates="datasets")
    measurements: Mapped[list["Measurement"]] = relationship(back_populates="dataset")


class Measurement(Base):
    """A single recorded dice count for one player at one roll of an activity."""

    __tablename__ = "measurements"

    id: Mapped[int] = mapped_column(primary_key=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("student_datasets.id"))
    player: Mapped[int] = mapped_column(SmallInteger)
    roll_number: Mapped[int] = mapped_column(SmallInteger)
    dice_count: Mapped[int] = mapped_column(SmallInteger)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    dataset: Mapped["StudentDataset"] = relationship(back_populates="measurements")
