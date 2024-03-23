from datetime import date

from pydantic import BaseModel


class CreateTaskBody(BaseModel):
    title: str | None
    description: str | None
    deadline: date
    responsible_user_id: int
    days_for_completion: int
