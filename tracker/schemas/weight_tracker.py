from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class WeightTrackerSchema(BaseModel):
    id: int
    user_id: int
    date: datetime
    weight: float

    model_config = ConfigDict(from_attributes=True)
