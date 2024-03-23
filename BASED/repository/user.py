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
        Получает информации о списаниях по ID пользователя
        """
        sql = """
        INSERT INTO "user" (name)
        VALUES ($1)
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql,name)
        return
    async def get_users(self) -> list[User]:
        """
        Получает информации о списаниях по ID пользователя
        """
        sql = """
            SELECT *
            FROM "user"
        """
        async with self._db.acquire() as c:
            data = await c.fetch(sql)

        return [User(**dict(i)) for i in data]
