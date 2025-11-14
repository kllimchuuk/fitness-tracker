from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class WorkoutSessionSchema(BaseModel):
    id: int
    user_id: int
    plan_id: int
    duration_minutes: int
    status: str
    start_time: datetime

    model_config = ConfigDict(from_attributes=True)
