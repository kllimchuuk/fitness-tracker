from pydantic import BaseModel


class ExerciseSetSchema(BaseModel):
    id: int
    exercise_id: int
    exercise_name: str
    sets: int
    reps: int
    weight: float
