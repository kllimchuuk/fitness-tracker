from datetime import datetime

from pydantic import BaseModel
from pydantic import ConfigDict


class ExerciseSchema(BaseModel):
    id: int
    name: str
    type: str
    description: str
    primary_muscle: str
    equipment: str
    archived_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
