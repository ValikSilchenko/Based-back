import logging

from fastapi import APIRouter

from BASED.state import app_state

from .models import GetUsersResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    path="/users",
    response_model=GetUsersResponse,
)
async def get_users():
    users = await app_state.user_repo.get_users()
    return GetUsersResponse(users=users)
