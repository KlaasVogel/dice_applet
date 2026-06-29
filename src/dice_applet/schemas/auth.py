from pydantic import BaseModel


class LoginRequest(BaseModel):
    email: str = ""
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    school_id: int | None = None
    new_school_name: str | None = None


class MeResponse(BaseModel):
    role: str
    teacher_id: int | None = None
    email: str | None = None
