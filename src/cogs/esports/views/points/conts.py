from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class Team(BaseModel):
    id: str = Field(default_factory=uuid4)
    name: str
    matches: str
    kills: int
    placepts: int
    totalpts: int
