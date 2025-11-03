from pydantic import BaseModel
from pydantic import ConfigDict


class WorkoutPlanSchema(BaseModel):
    id: int
    name: str
    version: int
    description: str

    model_config = ConfigDict(from_attributes=True)
