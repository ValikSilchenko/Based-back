from datetime import date

from pydantic import BaseModel

from BASED.repository.task import ShortTask, TaskStatusEnum


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


class TaskDependencyBody(BaseModel):
    task_id: int
    depends_of_task_id: int


class ArchiveTaskBody(BaseModel):
    task_id: int


class EditTaskDeadlineBody(BaseModel):
    task_id: int
    new_deadline: date


class GetAllTasksResponse(BaseModel):
    tasks: list[ShortTask]
