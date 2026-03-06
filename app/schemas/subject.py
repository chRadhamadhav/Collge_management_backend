from pydantic import BaseModel

class SubjectResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    code: str
    department_id: str
