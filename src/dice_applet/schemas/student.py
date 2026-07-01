from pydantic import BaseModel


class StudentJoinRequest(BaseModel):
    classroom_code: str


class StudentJoinResponse(BaseModel):
    animal_name: str
    personal_code: str
    classroom_id: int
    classroom_name: str
    suggested_name: str | None = None
    suggested_code: str | None = None


class StudentReconnectRequest(BaseModel):
    personal_code: str


class StudentReconnectResponse(BaseModel):
    animal_name: str
    personal_code: str
    classroom_id: int
    classroom_name: str


class StudentMe(BaseModel):
    student_id: int
    animal_name: str
    personal_code: str
    classroom_id: int
    classroom_name: str


class MeasurementOut(BaseModel):
    id: int
    player: int
    roll_number: int
    dice_count: int


class MeasurementIn(BaseModel):
    roll_number: int
    dice_count: int


class MeasurementBulkRequest(BaseModel):
    player: int
    rows: list[MeasurementIn]


class ActivityStatus(BaseModel):
    activity: int
    dataset_id: int
    is_locked: bool
    unlock_requested: bool
    measurement_count: int


class DatasetDetail(BaseModel):
    dataset_id: int
    activity: int
    is_locked: bool
    unlock_requested: bool
    measurements: list[MeasurementOut]
