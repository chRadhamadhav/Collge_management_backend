from pydantic import BaseModel

class SubjectCreate(BaseModel):
    name: str
    code: str
    department_id: str
    staff_id: str | None = None

class SubjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    code: str
    department_id: str
    staff_id: str | None = None
