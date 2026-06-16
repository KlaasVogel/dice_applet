from pydantic import BaseModel


class StudentSummary(BaseModel):
    id: int
    animal_name: str
    personal_code: str


class ClassroomDetailResponse(BaseModel):
    id: int
    name: str
    join_code: str
    is_active: bool
    students: list[StudentSummary]
