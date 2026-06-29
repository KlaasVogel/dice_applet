from datetime import datetime

from pydantic import BaseModel


class PendingRequestItem(BaseModel):
    id: int
    teacher_email: str
    school_name: str
    status: str
    requested_at: datetime


class SchoolItem(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime


class TeacherItem(BaseModel):
    id: int
    email: str
    created_at: datetime
    schools: list[dict]
