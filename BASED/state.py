import json
from concurrent.futures import ThreadPoolExecutor

from asyncpg import Pool, create_pool

import BASED.conf as conf


class AppState:
    def __init__(self) -> None:
        self._db = None

    async def init_connection(self, conn):
        await conn.set_type_codec(
            "jsonb",
            encoder=json.dumps,
            decoder=json.loads,
            schema="pg_catalog",
        )

    async def startup(self, from_tasks: bool = False) -> None:
        self._db = await create_pool(
            dsn=conf.DATABASE_DSN, init=self.init_connection
        )

    async def shutdown(self) -> None:
        if self._db:
            await self._db.close()

    @property
    def db(self) -> Pool:
        assert self._db
        return self._db


app_state = AppState()
