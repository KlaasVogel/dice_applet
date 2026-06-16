from pydantic import BaseModel


class StudentJoinRequest(BaseModel):
    classroom_code: str


class StudentJoinResponse(BaseModel):
    animal_name: str
    personal_code: str
    suggested_name: str | None = None
    suggested_code: str | None = None


class StudentReconnectRequest(BaseModel):
    personal_code: str


class StudentReconnectResponse(BaseModel):
    animal_name: str
    classroom_id: int
