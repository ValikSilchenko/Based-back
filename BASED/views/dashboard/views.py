import logging

from fastapi import APIRouter

from BASED.repository.task import TaskStatusEnum
from BASED.state import app_state
from BASED.views.dashboard.helpers import (
    get_status_order_number,
    get_warnings_list,
)
from BASED.views.dashboard.models import (
    DashboardTask,
    DashboardTasksByStatus,
    GetDashboardTasksResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["dashboard"])


@router.get(path="/dashboard_tasks", response_model=GetDashboardTasksResponse)
async def get_dashboard_tasks():
    tasks = await app_state.task_repo.get_tasks_ordered_by_status()

    statuses = {}
    for task in tasks:
        responsible = await app_state.user_repo.get_by_id(
            id_=task.responsible_user_id
        )
        warnings_list = get_warnings_list(task)
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

    progress = int(len(statuses[TaskStatusEnum.done]) / len(tasks) * 100)

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
