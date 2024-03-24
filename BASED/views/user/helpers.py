from BASED.views.dashboard.models import WarningModel, WarningTypeEnum


def get_message_for_task(warning: WarningModel):
    match warning.type:
        case WarningTypeEnum.start_soft:
            return "Рекомендуем приступить к задаче"
        case WarningTypeEnum.start_hard:
            return "Рекомендуем срочно приступить к задаче"
        case WarningTypeEnum.finish_soft:
            return "Рекомендуем завершить задачу"
        case WarningTypeEnum.finish_hard:
            return "Рекомендуем срочно завершить задачу"
        case WarningTypeEnum.cross_soft:
            return "Дедлайн задачи(${task_id}) пересекает эту задачу"
        case WarningTypeEnum.cross_hard:
            return "Дедлайн задачи(${task_id}) сильно пересекает эту задачу"
        case WarningTypeEnum.late_deadline:
            return "Дедлайн просрочен"
