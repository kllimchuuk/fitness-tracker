from pydantic import BaseModel
from pydantic import ConfigDict


class ExerciseSchema(BaseModel):
    id: int
    name: str
    type: str
    description: str

    model_config = ConfigDict(from_attributes=True)
