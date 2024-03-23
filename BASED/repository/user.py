from asyncpg import Pool


class UserRepository:
    def __init__(self, db: Pool):
        self._db = db


