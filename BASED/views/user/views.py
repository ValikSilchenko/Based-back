import logging

from fastapi import APIRouter, HTTPException

from starlette import status
from BASED.state import app_state
from BASED.views.user.models import CreateUserBody, GetUsersResponse, DeleteUserBody

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
async def del_users(body:DeleteUserBody):
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