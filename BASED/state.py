import json
from concurrent.futures import ThreadPoolExecutor

from asyncpg import Pool, create_pool

import BASED.conf as conf
from BASED.repository.user import UserRepository
from BASED.repository.variable import VariableRepository
from BASED.repository.task import TaskRepository


class AppState:
    def __init__(self) -> None:
        self._db = None
        self._user = None
        self._variable = None
        self._task = None

    async def init_connection(self, conn):
        await conn.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

    async def startup(self) -> None:
        self._db = await create_pool(
            dsn=conf.DATABASE_DSN, init=self.init_connection
        )
        self._user = UserRepository(db=self._db)

    async def shutdown(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> Pool:
        assert self._db
        return self._db

    @property
    def user_repo(self) -> UserRepository:
        assert self._user
        return self._user

    @property
    def variable_repo(self) -> VariableRepository:
        assert self._variable
        return self._variable

    @property
    def task_repo(self) -> TaskRepository:
        assert self._task
        return self._task



app_state = AppState()
