from pydantic import BaseModel


class TeacherLoginRequest(BaseModel):
    password: str


class ClassroomCreateRequest(BaseModel):
    name: str


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
