import logging

from fastapi import APIRouter

from BASED.repository.task import TaskCreate, TaskStatusEnum
from BASED.state import app_state
from BASED.views.task.models import CreateTaskBody

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(path="/create_task")
async def create_task(body: CreateTaskBody):
    await app_state.task_repo.create(
        task_create_model=TaskCreate(status=TaskStatusEnum.to_do, **dict(body))
    )
