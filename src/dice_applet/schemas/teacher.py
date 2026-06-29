from pydantic import BaseModel


class ClassroomCreateRequest(BaseModel):
    name: str
    school_id: int


class ClassroomCreateResponse(BaseModel):
    id: int
    name: str
    join_code: str


class ClassroomListItem(BaseModel):
    id: int
    name: str
    join_code: str
    is_active: bool
    student_count: int


class SchoolItem(BaseModel):
    id: int
    name: str


class PendingSchoolRequestItem(BaseModel):
    id: int
    teacher_email: str
    school_name: str
    requested_at: str
