import logging

from BASED.repository.task import DependencyTypeEnum
from BASED.state import app_state
from BASED.views.task.models import CreationTaskDependencies, TaskDependency

logger = logging.getLogger(__name__)


async def check_dependency_and_add(
    dependencies: list[TaskDependency],
) -> list[TaskDependency]:
    depend_errors = list()
    for depend in dependencies:
        task_exist = await app_state.task_repo.get_by_id(id_=depend.task_id)
        if not task_exist:
            logger.error("Task not found. task_id=%s", depend.task_id)
            depend_errors.append(depend)
            continue
        depends_task_exist = await app_state.task_repo.get_by_id(
            id_=depend.depends_of_task_id
        )
        if not depends_task_exist:
            logger.error("Task not found. task_id=%s", depend.task_id)
            depend_errors.append(depend)
            continue
        if task_exist == depends_task_exist:
            logger.error(
                "Сannot refer to itself. task_id=%s task_depend_id=%s",
                depend.task_id,
                depend.depends_of_task_id,
            )
            depend_errors.append(depend)
            continue
        depends_task_list = [depend.depends_of_task_id]
        logger.info(f"now: {depend.depends_of_task_id}")
        dependend_task = await app_state.task_repo.get_task_depends(
            id_=depend.depends_of_task_id
        )
        ok = True
        if dependend_task:
            while dependend_task:
                logger.info(f"in cycle: {dependend_task}")
                for x in dependend_task:
                    depends_task_list.append(x.depends_task_id)
                    dependend_task = (
                        await app_state.task_repo.get_task_depends(
                            id_=x.depends_task_id
                        )
                    )
            logger.info(f"after cycle res: {depends_task_list}")
            if depend.task_id in depends_task_list:
                logger.error(
                    "Depend creating cycle."
                    " task_id=%s in depends_task_list=%s",
                    depend.task_id,
                    depends_task_list,
                )
                ok = False
        if not ok:
            depend_errors.append(depend)
            continue
        else:
            await app_state.task_repo.add_task_depends(
                id_=depend.task_id, depends_id=depend.depends_of_task_id
            )
    return depend_errors


def parse_dependencies_types_to_task_depends(
    dependencies: list[CreationTaskDependencies], main_task_id: int
) -> list[TaskDependency]:
    dependencies = [
        TaskDependency(
            task_id=(
                dependency.task_id
                if dependency.type == DependencyTypeEnum.depends_of
                else main_task_id
            ),
            depends_of_task_id=(
                main_task_id
                if dependency.type == DependencyTypeEnum.depends_of
                else dependency.task_id
            ),
        )
        for dependency in dependencies
    ]

    return dependencies
