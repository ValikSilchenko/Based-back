import json

from asyncpg import Pool, create_pool

import BASED.conf as conf
from BASED.clients.mailing import MailClient
from BASED.repository.task import TaskRepository
from BASED.repository.user import UserRepository
from BASED.repository.variable import VariableRepository


class AppState:
    def __init__(self) -> None:
        self._db = None
        self._user = None
        self._variable = None
        self._task = None
        self._mail_client = None

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
        self._task = TaskRepository(db=self._db)
        self._mail_client = MailClient(
            host=conf.SMTP_HOST,
            port=conf.SMTP_PORT,
            username=conf.SMTP_USERNAME,
            password=conf.SMTP_PASSWORD,
        )

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

    @property
    def mail_client(self) -> MailClient:
        assert self._mail_client
        return self._mail_client


app_state = AppState()
