from asyncpg import Pool


class TaskRepository:
    def __init__(self, db: Pool):
        self._db = db