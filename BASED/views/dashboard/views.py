import logging

from fastapi import APIRouter

from BASED.repository.task import TaskStatusEnum
from BASED.state import app_state
from BASED.views.dashboard.helpers import (
    get_start_finish_date,
    get_status_order_number,
    get_warnings_with_cross,
)
from BASED.views.dashboard.models import (
    DashboardTask,
    DashboardTasksByStatus,
    GetDashboardTasksResponse,
    GetTimelineDependenciesResponse,
    GetTimelineTasksResponse,
    TimelineTask,
    TimelineTaskDependency,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get(path="/dashboard_tasks", response_model=GetDashboardTasksResponse)
async def get_dashboard_tasks():
    tasks = await app_state.task_repo.get_tasks_ordered_by_deadline()

    statuses = {}
    for task in tasks:
        responsible = await app_state.user_repo.get_by_id(
            id_=task.responsible_user_id
        )
        warnings_list = await get_warnings_with_cross(task)
        dashboard_task = DashboardTask(
            id=task.id,
            title=task.title,
            deadline=task.deadline,
            responsible=responsible,
            warnings=warnings_list,
        )
        if task.status in statuses:
            statuses[task.status].append(dashboard_task)
        else:
            statuses[task.status] = [dashboard_task]

    progress = int(
        len(statuses.get(TaskStatusEnum.done, [])) / len(tasks) * 100
    )

    return GetDashboardTasksResponse(
        progress=progress,
        statuses=[
            DashboardTasksByStatus(
                status_name=status,
                order_number=get_status_order_number(status),
                tasks=tasks_by_status,
            )
            for status, tasks_by_status in statuses.items()
        ],
    )


@router.get("/timeline_tasks", response_model=GetTimelineTasksResponse)
async def get_timeline_tasks():
    tasks = await app_state.task_repo.get_tasks_ordered_by_deadline()
    timeline_tasks = []
    for task in tasks:
        responsible = await app_state.user_repo.get_by_id(
            id_=task.responsible_user_id
        )
        warnings_list = await get_warnings_with_cross(task)
        start_date, finish_date = get_start_finish_date(task)

        timeline_tasks.append(
            TimelineTask(
                id=task.id,
                status=task.status,
                title=task.title,
                deadline=task.deadline,
                start_date=start_date,
                finish_date=finish_date,
                responsible=responsible,
                warnings=warnings_list,
            )
        )

    return GetTimelineTasksResponse(tasks=timeline_tasks)


@router.get(
    path="/timeline_dependencies",
    response_model=GetTimelineDependenciesResponse,
)
async def get_timeline_dependencies(task_id: int):
    task = await app_state.task_repo.get_by_id(id_=task_id)
    dependencies = await app_state.task_repo.get_all_task_dependencies(
        task_id=task.id
    )

    tasks = []
    for dependency in dependencies:
        responsible = await app_state.user_repo.get_by_id(
            id_=dependency.responsible_user_id
        )

        task = await app_state.task_repo.get_by_id(id_=dependency.id)
        warnings_list = await get_warnings_with_cross(task)
        start_date, finish_date = get_start_finish_date(task)

        tasks.append(
            TimelineTaskDependency(
                id=task.id,
                warnings=warnings_list,
                start_date=start_date,
                finish_date=finish_date,
                responsible=responsible,
                dependency_type=dependency.dependency_type,
                status=task.status,
                title=task.title,
                deadline=task.deadline,
            )
        )

    return GetTimelineDependenciesResponse(tasks=tasks)
