import logging
from datetime import date

from asyncpg import ForeignKeyViolationError
from fastapi import APIRouter, HTTPException
from starlette import status

from BASED.repository.task import (
    DependencyTypeEnum,
    TaskCreate,
    TaskStatusEnum,
)
from BASED.state import app_state
from BASED.views.task.helpers import check_dependency_and_add
from BASED.views.task.models import (
    ArchiveTaskBody,
    CreateTaskResponse,
    EditTaskBody,
    EditTaskDeadlineBody,
    GetAllTasksResponse,
    ListTaskDependency,
    TaskBody,
    TaskDependency,
    UpdateTaskStatusBody,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(path="/create_task", response_model=CreateTaskResponse)
async def create_task(body: TaskBody):
    try:
        task = await app_state.task_repo.create(
            task_create_model=TaskCreate(
                status=TaskStatusEnum.to_do, **dict(body)
            )
        )
        logger.info("Task created successfully. task_id=%s", task.id)

        dependencies = [
            TaskDependency(
                task_id=(
                    dependency.task_id
                    if dependency.type == DependencyTypeEnum.depends_of
                    else task.id
                ),
                depends_of_task_id=(
                    task.id
                    if dependency.type == DependencyTypeEnum.depends_of
                    else dependency.task_id
                ),
            )
            for dependency in body.dependencies
        ]
        depend_errors = await check_dependency_and_add(dependencies)
    except ForeignKeyViolationError:
        logger.error(
            "Responsible user not found. responsible_user_id=%s",
            body.responsible_user_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Responsible user not found.",
        )

    return CreateTaskResponse(
        created_task_id=task.id, dependency_errors=depend_errors
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
async def add_task_dependency(body: ListTaskDependency):
    if len(body.dependencies) < 0:
        return

    depend_errors = await check_dependency_and_add(
        dependencies=body.dependencies
    )

    return depend_errors


@router.delete(path="/del_task_dependency")
async def delete_task_dependency(body: TaskDependency):
    is_deleted = await app_state.task_repo.del_tasks_depends(
        body.task_id, body.depends_of_task_id
    )
    logger.info(is_deleted)
    if not is_deleted:
        logger.error(
            "Dependency not found. task_id=%s depends_of_task_id=%s",
            body.task_id,
            body.depends_of_task_id,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dependency not found.",
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
