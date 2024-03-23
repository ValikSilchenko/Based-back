import logging
from datetime import datetime

from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, HTTPException
from starlette import status

from BASED.repository.task import TaskCreate, TaskStatusEnum
from BASED.state import app_state
from BASED.views.task.models import (
    EditTaskBody,
    TaskBody,
    UpdateTaskStatusBody,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(path="/create_task")
async def create_task(body: TaskBody):
    try:
        await app_state.task_repo.create(
            task_create_model=TaskCreate(
                status=TaskStatusEnum.to_do, **dict(body)
            )
        )
    except ForeignKeyViolationError:
        logger.error(
            "Responsible user not found. responsible_user_id=%s",
            body.responsible_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Responsible user not found.",
        )


@router.put(path="/edit_task")
async def edit_task(body: EditTaskBody):
    try:
        task = await app_state.task_repo.update_task_data(
            task_id=body.task_id, **dict(body.task_data)
        )
    except ForeignKeyViolationError:
        logger.error(
            "Responsible user not found. responsible_user_id=%s",
            body.task_data.responsible_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Responsible user not found.",
        )
    if not task:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task not found.",
        )


@router.put(path="/update_task_status")
async def update_task_status(body: UpdateTaskStatusBody):
    old_task = await app_state.task_repo.get_by_id(id_=body.task_id)
    if not old_task:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found."
        )

    updated_task = await app_state.task_repo.update_task_status(
        task_id=body.task_id, new_status=body.new_status
    )

    match updated_task.status:
        case TaskStatusEnum.to_do:
            await app_state.task_repo.update_task_start_finish_dates(
                task_id=updated_task.id,
                new_start_date=None,
                new_finish_date=None,
            )
        case TaskStatusEnum.in_progress:
            await app_state.task_repo.update_task_start_finish_dates(
                task_id=updated_task.id,
                new_start_date=(
                    datetime.today()
                    if old_task.status == TaskStatusEnum.to_do
                    else updated_task.actual_start_date
                ),
                new_finish_date=None,
            )
        case TaskStatusEnum.done:
            if old_task.status == TaskStatusEnum.to_do:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Task cannot be done immediately from to_do",
                )

            await app_state.task_repo.update_task_start_finish_dates(
                task_id=updated_task.id,
                new_start_date=updated_task.actual_start_date,
                new_finish_date=(
                    datetime.today()
                    if old_task.status != TaskStatusEnum.done
                    else updated_task.actual_start_date
                ),
            )
