import json
import logging
from enum import StrEnum

from asyncpg import Pool
from asyncpg.exceptions import (
    IntegrityConstraintViolationError as ConstraintError,
)
from pydantic import BaseModel, computed_field

from BASED.helpers import assert_never

logger = logging.getLogger(__name__)


class VariableTypeEnum(StrEnum):
    str = "str"
    int = "int"
    dict = "dict"


class VariableEnum(StrEnum):
    empty_tag = "empty_tag"
    ind_ind_template_tag = "ind_ind_template"
    ind_jur_template_tag = "ind_jur_template"
    jur_ind_template_tag = "jur_ind_template"
    standart_pack_amount = "standart_pack_amount"
    medium_pack_amount = "medium_pack_amount"
    big_pack_amount = "big_pack_amount"
    huge_pack_amount = "huge_pack_amount"


class Variable(BaseModel):
    """
    Переменная проекта.
    """

    name: VariableEnum
    type: VariableTypeEnum
    value: str

    @computed_field
    @property
    def parsed_value(self) -> str | int | dict | None:
        parsed_value = None
        match self.type:
            case VariableTypeEnum.str:
                parsed_value = self.value
            case VariableTypeEnum.int:
                parsed_value = int(self.value)
            case VariableTypeEnum.dict:
                parsed_value = json.loads(self.value)
            case _:
                assert_never()
        return parsed_value


class VariableRepository:
    def __init__(self, db: Pool) -> None:
        self._db = db

    async def init_variables(self, variable_list: list[Variable]):
        """
        Инициализирует переменные в базе (если они еще не созданы)
        """
        logger.info("Initialization variables, count=%s", len(variable_list))
        for variable in variable_list:
            try:
                created_value = await self._create_variable(variable)
                logger.info(
                    "Variable '%s' was created with value '%s'",
                    created_value.name,
                    created_value.value,
                )
            except ConstraintError:
                pass

    async def _create_variable(self, variable: Variable) -> Variable:
        """
        Создает переменную
        """
        sql = """
            INSERT INTO "variable"
            (name, type, value)
            VALUES ($1, $2, $3)
            RETURNING *
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(
                sql, variable.name, variable.type, variable.value
            )

        if not row:
            return

        return Variable(**dict(row))

    async def get_variable(self, name: str) -> Variable | None:
        """
        Получает значение переменной по имени
        """
        sql = """
            SELECT *
            FROM "variable"
            WHERE "name" = $1
        """
        async with self._db.acquire() as c:
            row = await c.fetchrow(sql, name)

        if not row:
            return

        return Variable(**dict(row))
