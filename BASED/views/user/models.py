from pydantic import BaseModel

from BASED.repository.user import User


class GetUsersResponse(BaseModel):
    users: list[User]
