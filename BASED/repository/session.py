from datetime import datetime
from secrets import token_urlsafe

from asyncpg import Pool
from pydantic import BaseModel

from . import helpers


class Session(BaseModel):
    id: str
    telegram_id: str
    user_id: int | None = None
    ip: str | None = None
    user_agent: str | None = None
    is_active: bool
    created_timestamp: datetime


class SessionCreate(BaseModel):
    id: str
    telegram_id: str
    ip: str | None = None
    user_agent: str | None = None
    is_active: bool


class SessionRepository:
    def __init__(self, db: Pool) -> None:
        self._db = db

    async def get(self, _id: str) -> Session | None:
        """
        Получает сессию.
        """
        sql = """
            SELECT
                "session".*,
                "user"."id" AS "user_id"
            FROM "session"
            LEFT JOIN "user"
                ON "user"."telegram_id"
                    =
                    "session"."telegram_id"
            WHERE "session"."id" = $1
            """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, _id)

        if not row:
            return

        return Session(**dict(row))

    async def create(
        self,
        telegram_id: str,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> SessionCreate:
        """
        Создает сессию.
        """
        session = SessionCreate(
            id=token_urlsafe(32),
            telegram_id=telegram_id,
            ip=ip,
            user_agent=user_agent,
            is_active=True,
        )
        model_sql = helpers.build_model_sql(session)
        sql = f"""
            INSERT INTO "session" ({model_sql.field_names})
            VALUES ({model_sql.placeholders})
        """
        async with self._db.acquire() as c:
            await c.execute(sql, *model_sql.values)

        return session
