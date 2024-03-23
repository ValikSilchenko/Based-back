import logging

from fastapi import APIRouter

from BASED.repository.task import TaskCreate
from BASED.state import app_state

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(path="/create_task")
async def create_task(body: TaskCreate):
    await app_state.task_repo.create(task_create_model=body)
