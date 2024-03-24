import logging
from datetime import date, timedelta

from BASED.conf import TIME_RESERVE_COEF
from BASED.repository.task import Task, TaskStatusEnum, TaskStatusOrder
from BASED.state import app_state
from BASED.views.dashboard.models import WarningModel, WarningTypeEnum

logger = logging.getLogger(__name__)


def get_warnings_list(task: Task) -> list[WarningModel]:
    warnings = []
    current_date = date.today()
    match task.status:
        case TaskStatusEnum.to_do:
            if current_date >= task.deadline - timedelta(
                days=task.days_for_completion
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.start_hard, task_id=task.id
                    )
                )
            elif current_date >= task.deadline - timedelta(
                days=task.days_for_completion * TIME_RESERVE_COEF
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.start_soft, task_id=task.id
                    )
                )
        case TaskStatusEnum.in_progress:
            days_in_work = (current_date - task.actual_start_date).days
            days_to_deadline = task.days_for_completion - days_in_work
            if days_to_deadline < 0:
                days_to_deadline = 0

            if current_date >= task.deadline - timedelta(
                days=days_to_deadline
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.finish_hard, task_id=task.id
                    )
                )
            elif current_date >= task.deadline - timedelta(
                days=days_to_deadline * TIME_RESERVE_COEF
            ):
                warnings.append(
                    WarningModel(
                        type=WarningTypeEnum.finish_soft, task_id=task.id
                    )
                )

    if task.status == TaskStatusEnum.done and task.actual_finish_date > task.deadline:
        warnings.append(
            WarningModel(type=WarningTypeEnum.late_deadline, task_id=task.id)
        )
    elif task.status != TaskStatusEnum.done and current_date > task.deadline:
        warnings.append(
            WarningModel(type=WarningTypeEnum.late_deadline, task_id=task.id)
        )

    return warnings


async def get_warnings_with_cross(task: Task) -> list[WarningModel]:
    warnings = get_warnings_list(task)
    dependent_of_tasks = await app_state.task_repo.get_tasks_dependent_of(
        dependent_task_id=task.id
    )
    if not dependent_of_tasks:
        return warnings

    tasks = []
    for dependency in dependent_of_tasks:
        tasks.append(await app_state.task_repo.get_by_id(id_=dependency.task_id))

    comparing_task = max(tasks, key=lambda x: x.deadline)

    soft_start_date = task.deadline - timedelta(
        days=task.days_for_completion * TIME_RESERVE_COEF
    )
    hard_start_date = task.deadline - timedelta(days=task.days_for_completion)
    current_date = date.today()

    cross_warning = None
    if (
        comparing_task.actual_finish_date
        and comparing_task.actual_finish_date >= hard_start_date
    ):
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_hard,
            task_id=comparing_task.id,
        )
    elif (
        comparing_task.actual_finish_date
        and comparing_task.actual_finish_date >= soft_start_date
    ):
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_soft,
            task_id=comparing_task.id,
        )
    if (
        comparing_task.actual_finish_date is None
        and current_date > hard_start_date
    ):
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_hard,
            task_id=comparing_task.id,
        )
    elif (
        comparing_task.actual_finish_date is None
        and current_date > soft_start_date
    ):
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_soft,
            task_id=comparing_task.id,
        )

    if comparing_task.deadline > hard_start_date:
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_hard,
            task_id=comparing_task.id,
        )
    elif comparing_task.deadline > soft_start_date:
        cross_warning = WarningModel(
            type=WarningTypeEnum.cross_soft,
            task_id=comparing_task.id,
        )

    if cross_warning:
        warnings.append(cross_warning)

    return warnings


def get_status_order_number(status: TaskStatusEnum) -> int:
    match status:
        case TaskStatusEnum.to_do:
            return TaskStatusOrder.to_do.value
        case TaskStatusEnum.in_progress:
            return TaskStatusOrder.in_progress.value
        case TaskStatusEnum.done:
            return TaskStatusOrder.done.value


def get_start_finish_date(task: Task) -> tuple[date, date]:
    """
    Получает предполагаемую дату начала и окончания работы на задачей.
    """
    current_date = date.today()
    match task.status:
        case TaskStatusEnum.done:
            start_date = task.actual_start_date
            finish_date = task.actual_finish_date
        case TaskStatusEnum.in_progress:
            start_date = task.actual_start_date
            if current_date > task.deadline:
                finish_date = current_date
            else:
                finish_date = start_date + timedelta(
                    days=task.days_for_completion - 1
                )
        case TaskStatusEnum.to_do:
            days_with_reserve = int(
                task.days_for_completion * TIME_RESERVE_COEF
            )
            start_date_with_reserve = task.deadline - timedelta(
                days=days_with_reserve
            )
            if current_date < start_date_with_reserve:
                start_date = start_date_with_reserve
                finish_date = start_date_with_reserve + timedelta(
                    days=task.days_for_completion - 1
                )
            else:
                start_date = current_date
                finish_date = current_date + timedelta(
                    days=task.days_for_completion - 1
                )

    return start_date, finish_date
