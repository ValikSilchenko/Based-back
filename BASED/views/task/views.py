import logging
from datetime import date

from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, HTTPException
from starlette import status

from BASED.repository.task import TaskCreate, TaskStatusEnum
from BASED.state import app_state
from BASED.views.task.models import (
    ArchiveTaskBody,
    EditTaskBody,
    EditTaskDeadlineBody,
    GetAllTasksResponse,
    TaskBody,
    TaskDependencyBody,
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
                    date.today()
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
                    date.today()
                    if old_task.status != TaskStatusEnum.done
                    else updated_task.actual_start_date
                ),
            )


@router.post(path="/add_task_dependency")
async def add_task_dependency(body: TaskDependencyBody):
    task_exist = await app_state.task_repo.get_by_id(id_=body.task_id)
    if not task_exist:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found."
        )
    depends_task_exist = await app_state.task_repo.get_by_id(
        id_=body.depends_of_task_id
    )
    if not depends_task_exist:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found."
        )
    if task_exist == depends_task_exist:
        logger.error(
            "Сannot refer to itself. task_id=%s task_depend_id=%s",
            body.task_id,
            body.depends_of_task_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Сannot refer to itself.",
        )
    depends_task_list = [body.depends_of_task_id]
    dependend_task = await app_state.task_repo.get_task_depends(
        id_=body.depends_of_task_id
    )
    if dependend_task:
        while dependend_task:
            depends_task_list.append(dependend_task.depends_task_id)
            dependend_task = await app_state.task_repo.get_task_depends(
                id_=dependend_task.depends_task_id
            )
        if body.task_id in depends_task_list:
            logger.error(
                "Depend creating cycle. task_id=%s in depends_task_list=%s",
                body.task_id,
                depends_task_list,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Depend creating cycle.",
            )

    await app_state.task_repo.add_task_depends(
        id_=body.task_id, depends_id=body.depends_of_task_id
    )
    return None

@router.delete(
    path="/del_task_dependency"
)
async def delete_task_dependency(body:TaskDependencyBody):
    is_deleted = await app_state.task_repo.del_tasks_depends(
        body.task_id,
        body.depends_of_task_id
    )
    logger.info(is_deleted)
    if not is_deleted:
        logger.error("Dependency not found. task_id=%s depends_of_task_id=%s",
                     body.task_id, body.depends_of_task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Dependency not found."
        )
    return

@router.put(path="/archive_task")
async def archive_task(body: ArchiveTaskBody):
    result = await app_state.task_repo.update_task_archive_status(
        task_id=body.task_id, archive_status=True
    )
    if not result:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found."
        )


@router.put(path="/edit_deadline")
async def edit_task_deadline(body: EditTaskDeadlineBody):
    result = await app_state.task_repo.update_task_deadline(
        task_id=body.task_id, new_deadline=body.new_deadline
    )
    if not result:
        logger.error("Task not found. task_id=%s", body.task_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Task not found."
        )

@router.get(
    path="/all_tasks",
)
async def get_all_tasks():
    tasks = await app_state.task_repo.get_all_short_tasks()
    return GetAllTasksResponse(tasks=tasks)