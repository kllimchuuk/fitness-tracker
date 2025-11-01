from pydantic import BaseModel


class WorkoutPlanSchema(BaseModel):
    id: int
    name: str
    version: int
    description: str
