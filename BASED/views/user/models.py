from pydantic import BaseModel

from BASED.repository.user import User


class CreateUserBody(BaseModel):
    name: str


class GetUsersResponse(BaseModel):
    users: list[User]

class DeleteUserBody(BaseModel):
    user_id: int