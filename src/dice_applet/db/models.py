import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class TeacherSchoolStatus(str, enum.Enum):
    pending_admin = "pending_admin"
    pending_school = "pending_school"
    approved = "approved"
    rejected = "rejected"


class School(Base):
    """A school that groups classrooms and teachers."""

    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    classrooms: Mapped[list["Classroom"]] = relationship(back_populates="school")
    teacher_links: Mapped[list["TeacherSchool"]] = relationship(back_populates="school")


class Teacher(Base):
    """A registered teacher; active when they have at least one approved TeacherSchool row."""

    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    school_links: Mapped[list["TeacherSchool"]] = relationship(
        back_populates="teacher",
        foreign_keys="TeacherSchool.teacher_id",
    )


class TeacherSchool(Base):
    """Junction table linking a teacher to a school, with an approval workflow."""

    __tablename__ = "teacher_schools"
    __table_args__ = (UniqueConstraint("teacher_id", "school_id", name="uq_teacher_school"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("teachers.id"))
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.id"))
    status: Mapped[TeacherSchoolStatus] = mapped_column(
        Enum(TeacherSchoolStatus, name="teacher_school_status"), nullable=False
    )
    resolved_by: Mapped[int | None] = mapped_column(ForeignKey("teachers.id"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teacher: Mapped["Teacher"] = relationship(back_populates="school_links", foreign_keys=[teacher_id])
    school: Mapped["School"] = relationship(back_populates="teacher_links")


class Classroom(Base):
    """A teacher-managed group that students join via a code."""

    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    join_code: Mapped[str] = mapped_column(String(5), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="1")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    school_id: Mapped[int | None] = mapped_column(ForeignKey("schools.id"), nullable=True)

    school: Mapped[School | None] = relationship(back_populates="classrooms")
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
