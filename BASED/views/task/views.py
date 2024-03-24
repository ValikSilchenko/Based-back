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
from BASED.repository.user import User
from BASED.state import app_state
from BASED.views.dashboard.helpers import get_warnings_with_cross
from BASED.views.task.helpers import check_dependency_and_add
from BASED.views.task.models import (
    ArchiveTaskBody,
    CustomDependencies,
    EditTaskBody,
    EditTaskDeadlineBody,
    GetAllTasksResponse,
    GetTasksDescriptionResponse,
    ListTaskDependency,
    TaskBody,
    TaskDependency,
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


@router.get(
    path="/task_description",
)
async def get_task_description(task_id: int):
    task = await app_state.task_repo.get_by_id(task_id)
    if task.responsible_user_id:
        responsible = await app_state.user_repo.get_by_id(
            id_=task.responsible_user_id
        )
    else:
        responsible = User(id=0, name=None)
    warnings = await get_warnings_with_cross(task)
    logger.info(warnings)
    task_depends = await app_state.task_repo.get_task_depends(id_=task_id)
    dependencies = list()
    for i in task_depends:
        i_task = await app_state.task_repo.get_by_id(i.depends_task_id)
        Cust_dep = CustomDependencies(
            warnings=await get_warnings_with_cross(i_task),
            **dict(i_task),
            type=DependencyTypeEnum.dependent_for,
        )
        dependencies.append(Cust_dep)
    task_depends_off = await app_state.task_repo.get_tasks_dependent_of(
        dependent_task_id=task_id
    )

    for i in task_depends_off:
        i_task = await app_state.task_repo.get_by_id(i.task_id)
        Cust_dep = CustomDependencies(
            warnings=await get_warnings_with_cross(i_task),
            **dict(i_task),
            type=DependencyTypeEnum.dependent_for,
        )
        dependencies.append(Cust_dep)

    return GetTasksDescriptionResponse(
        **dict(task),
        created_at=task.created_timestamp,
        responsible=responsible,
        warnings=warnings,
        dependencies=dependencies,
    )
