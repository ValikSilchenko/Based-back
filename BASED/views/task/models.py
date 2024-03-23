from datetime import date

from pydantic import BaseModel

from BASED.repository.task import TaskStatusEnum


class TaskBody(BaseModel):
    title: str | None
    description: str | None
    deadline: date
    responsible_user_id: int
    days_for_completion: int


class EditTaskBody(BaseModel):
    task_id: int
    task_data: TaskBody


class UpdateTaskStatusBody(BaseModel):
    task_id: int
    new_status: TaskStatusEnum


class ArchiveTaskBody(BaseModel):
    task_id: int


class EditTaskDeadlineBody(BaseModel):
    task_id: int
    new_deadline: date
