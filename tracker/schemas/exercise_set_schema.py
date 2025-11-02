from pydantic import BaseModel
from pydantic import ConfigDict


class ExerciseSetSchema(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str | None = None
    sets: int
    reps: int
    weight: float

    model_config = ConfigDict(from_attributes=True)
