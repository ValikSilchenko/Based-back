from typing import Optional

from asyncpg import Pool
from pydantic import BaseModel


class User(BaseModel):
    id: int
    name: str


class UserRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create_user(self, name):
        """
        Создаёт пользователя.
        """
        sql = """
        INSERT INTO "user" (name)
        VALUES ($1)
        """
        async with self._db.acquire() as c:
            await c.fetchrow(sql, name)
        return

    async def get_users(self) -> list[User]:
        """
        Получает всех пользователей.
        """
        sql = """
            SELECT *
            FROM "user"
        """
        async with self._db.acquire() as c:
            data = await c.fetch(sql)

        return [User(**dict(i)) for i in data]

    async def get_by_id(self, id_: int) -> Optional[User]:
        sql = """
            select * from "user"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return User(**dict(row))

    async def del_user(self, user_id: int) -> bool:
        """
        Удаление пользователя.
        """
        sql = """
            DELETE FROM "user"
            WHERE "id" = $1
            RETURNING TRUE
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, user_id)
        if not row:
            return False
        return True
