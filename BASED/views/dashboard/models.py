from datetime import date
from enum import StrEnum

from pydantic import BaseModel

from BASED.repository.task import DependencyTypeEnum, TaskStatusEnum
from BASED.repository.user import User


class WarningTypeEnum(StrEnum):
    start_soft = "start_soft"
    start_hard = "start_hard"
    finish_soft = "finish_soft"
    finish_hard = "finish_hard"
    cross_soft = "cross_soft"
    cross_hard = "cross_hard"
    late_deadline = "late_deadline"


class WarningModel(BaseModel):
    type: WarningTypeEnum
    task_id: int


class DashboardTask(BaseModel):
    id: int
    title: str
    deadline: date
    responsible: User
    warnings: list[WarningModel]


class DashboardTasksByStatus(BaseModel):
    status_name: TaskStatusEnum
    order_number: int
    tasks: list[DashboardTask]


class GetDashboardTasksResponse(BaseModel):
    progress: int
    statuses: list[DashboardTasksByStatus]


class TimelineTask(BaseModel):
    id: int
    status: TaskStatusEnum
    title: str
    deadline: date
    start_date: date
    finish_date: date
    responsible: User
    warnings: list[WarningModel]


class GetTimelineTasksResponse(BaseModel):
    tasks: list[TimelineTask]


class TimelineTaskDependency(TimelineTask):
    dependency_type: DependencyTypeEnum


class GetTimelineDependenciesResponse(BaseModel):
    tasks: list[TimelineTaskDependency]
