from pydantic import BaseModel


class ExerciseSchema(BaseModel):
    id: int
    name: str
    type: str
    description: str
