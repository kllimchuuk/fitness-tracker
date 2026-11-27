from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class SetLogSchema(BaseModel):
    id: int
    session_id: int
    exercise_id: int
    set_number: int
    reps: int
    weight_kg: float
    rpe: float | None
    logged_at: datetime

    model_config = ConfigDict(from_attributes=True)
