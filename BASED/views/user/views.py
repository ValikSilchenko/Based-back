import logging

from fastapi import APIRouter

from BASED.state import app_state

from BASED.views.user.models import GetUsersResponse,CreateUserBody

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    path="/user",
)
async def create_users(body:CreateUserBody):
    await app_state.user_repo.create_user(body.name)

@router.get(
    path="/users",
    response_model=GetUsersResponse,
)
async def get_users():
    users = await app_state.user_repo.get_users()
    return GetUsersResponse(users=users)
