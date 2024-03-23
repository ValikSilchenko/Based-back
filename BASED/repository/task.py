from datetime import date, datetime
from enum import StrEnum
from typing import Optional

from asyncpg import Pool
from pydantic import BaseModel

from BASED.repository.helpers import build_model_sql


class TaskStatusEnum(StrEnum):
    to_do = "to_do"
    in_progress = "in_progress"
    done = "done"


class TaskCreate(BaseModel):
    status: TaskStatusEnum
    title: str | None
    description: str | None
    deadline: date
    responsible_user_id: int
    days_for_completion: int


class Task(BaseModel):
    id: int
    responsible_user_id: int
    status: TaskStatusEnum
    title: str | None
    description: str | None
    deadline: date
    days_for_completion: int
    actual_start_date: date | None
    actual_finish_date: date | None
    actual_completion_days: int | None
    is_archived: bool
    created_timestamp: datetime


class TaskRepository:
    def __init__(self, db: Pool):
        self._db = db

    async def create(self, task_create_model: TaskCreate) -> Task:
        model_build = build_model_sql(task_create_model)
        sql = f"""
            insert into "task" ({model_build.field_names})
            values ({model_build.placeholders})
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, *model_build.values)

        return Task(**dict(row))

    async def get_by_id(self, id_: int) -> Optional[Task]:
        sql = """
            select * from "task"
            where "id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)

        if not row:
            return

        return Task(**dict(row))

    async def update_task_data(
        self,
        task_id: int,
        title: str | None,
        description: str | None,
        deadline: date,
        responsible_user_id: int,
        days_for_completion: int,
    ) -> Optional[Task]:
        sql = """
            update "task"
            set "title" = $2, "description" = $3, "deadline" = $4,
            "responsible_user_id" = $5, "days_for_completion" = $6
            where "id" = $1
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql,
                task_id,
                title,
                description,
                deadline,
                responsible_user_id,
                days_for_completion,
            )

        if not row:
            return

        return Task(**dict(row))

    async def update_task_status(self, task_id: int, new_status: TaskStatusEnum) -> Optional[Task]:
        sql = """
            update "task" set "status" = $2
            where "id" = $1
            returning *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, new_status)

        if not row:
            return

        return Task(**dict(row))


