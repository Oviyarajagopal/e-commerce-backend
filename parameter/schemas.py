from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str


class TaskUpdate(BaseModel):
    description: str | None = None
    priority: str | None = None
    status: str | None = None