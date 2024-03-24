import logging

from fastapi import APIRouter, HTTPException
from starlette import status

from BASED.conf import USER_EMAIL
from BASED.repository.task import TaskStatusEnum
from BASED.state import app_state
from BASED.views.dashboard.helpers import get_warnings_with_cross
from BASED.views.user.helpers import get_message_for_task
from BASED.views.user.models import (
    CreateUserBody,
    DeleteUserBody,
    GetUsersResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    path="/user",
)
async def create_user(body: CreateUserBody):
    await app_state.user_repo.create_user(body.name)


@router.get(
    path="/users",
    response_model=GetUsersResponse,
)
async def get_users():
    users = await app_state.user_repo.get_users()
    return GetUsersResponse(users=users)


@router.delete(
    path="/user",
)
async def del_users(body: DeleteUserBody):
    await app_state.task_repo.del_responsible_user_id(user_id=body.user_id)
    is_deleted = await app_state.user_repo.del_user(body.user_id)
    if not is_deleted:
        logger.error(
            "User not found.",
            body.user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found.",
        )
    else:
        return


@router.get(path="/send_report")
async def send_report_to_user():
    tasks = await app_state.task_repo.get_tasks_ordered_by_deadline()

    statuses = {}
    for task in tasks:
        warnings_list = await get_warnings_with_cross(task)

        if task.status in statuses:
            statuses[task.status].append((warnings_list, task.id))
        else:
            statuses[task.status] = [(warnings_list, task.id)]

    progress = int(
        len(statuses.get(TaskStatusEnum.done, [])) / len(tasks) * 100
    )
    text = f"""
        Прогресс по проекту: {progress}%.
        Количество неначатых задач: {len(statuses.get(TaskStatusEnum.to_do, []))}.
        Количество задач, находящихся в работе: {len(statuses.get(TaskStatusEnum.in_progress, []))}.
        Количество завершённых задач: {len(statuses.get(TaskStatusEnum.done, []))}.\n
    """

    for status_name, values in statuses.items():
        if values[0]:
            text += f"\n Имеются не решённые вопросы по задаче {values[1]}."

    await app_state.mail_client.send_message(
        to=USER_EMAIL, subject="Test", text=text
    )
