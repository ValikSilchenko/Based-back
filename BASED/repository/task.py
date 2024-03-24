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


class ShortTask(BaseModel):
    id: int
    title: str


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


class TaskDepends(BaseModel):
    task_id: int
    depends_task_id: int
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
        """
        Обновляет основные данные о задаче.
        """
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

    async def update_task_status(
        self, task_id: int, new_status: TaskStatusEnum
    ) -> Optional[Task]:
        """
        Изменяет статус задачи.
        """
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

    async def update_task_start_finish_dates(
        self,
        task_id: int,
        new_start_date: date | None,
        new_finish_date: date | None,
    ) -> bool:
        """
        Обновляет фактическую дату начала и фактическую дату окончания
        в соответсвуии с переданными значениями.
        Возвращает True в случае успеха, False если задача не найдена.
        """
        actual_completion_days = None
        if new_start_date is not None and new_finish_date is not None:
            actual_completion_days = (
                new_finish_date - new_start_date
            ).days + 1

        sql = """
            update "task"
            set "actual_start_date" = $2,
                "actual_finish_date" = $3,
                "actual_completion_days" = $4
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql,
                task_id,
                new_start_date,
                new_finish_date,
                actual_completion_days,
            )

        return bool(row)

    async def get_task_depends(self, id_: int) -> TaskDepends | None:
        """
        Показывает зависимость задачи
        """
        sql = """
        SELECT * from "task_depends"
        WHERE "task_depends"."task_id" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_)
        if not row:
            return

        return TaskDepends(**dict(row))

    async def add_task_depends(self, id_: int, depends_id: int):
        """
        Добавляет зависимость задач
        """
        sql = """
        INSERT INTO "task_depends" (task_id, depends_task_id)
        VALUES ($1, $2)
        ON CONFLICT (task_id, depends_task_id) DO NOTHING
        """
        async with self._db.acquire() as c:
            await c.fetchrow(sql, id_, depends_id)
        return

    async def update_task_archive_status(
        self, task_id: int, archive_status: bool
    ) -> bool:
        """
        Изменяет статус архивации для задачи.
        """
        sql = """
            update "task"
            set "is_archived" = $2
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, archive_status)

        return bool(row)

    async def update_task_deadline(
        self, task_id: int, new_deadline: date
    ) -> bool:
        """
        Изменяет текущий дедлайн по задаче.
        """
        sql = """
            update "task"
            set "deadline" = $2
            where "id" = $1
            returning 1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, task_id, new_deadline)

        return bool(row)

    async def get_all_tasks(self) -> list[ShortTask]:
        """
        Получает всех пользователей.
        """
        sql = """
            SELECT *
            FROM "task"
        """
        async with self._db.acquire() as c:
            data = await c.fetch(sql)

        return [ShortTask(**dict(i)) for i in data]

    async def del_tasks_depends(self, id_: int, depends_id: int) -> bool:
        """
        Получает всех пользователей.
        """
        sql = """
            DELETE FROM "task_depends"
            WHERE "task_id" = $1 AND "depends_task_id" = $2
            RETURNING TRUE
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, id_, depends_id)
        if not row:
            return False
        return True