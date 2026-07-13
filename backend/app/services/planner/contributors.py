"""Deprecated: use app.services.execution.modules — kept for import BC."""

from app.services.execution.modules.habits import contribute_habits
from app.services.execution.modules.nutrition import contribute_nutrition
from app.services.execution.modules.planner_tasks import contribute_planner_tasks as contribute_plan_tasks
from app.services.execution.modules.workouts import contribute_workouts
from app.services.execution.registry import collect_candidates


def collect_all_candidates(db, plan, day, *, delay_first_meal, training_hour):
    from app.services.execution.candidates import ExecutionContext

    ctx = ExecutionContext(delay_first_meal=delay_first_meal, training_hour=training_hour)
    return collect_candidates(db, plan, day, ctx)


__all__ = [
    'contribute_plan_tasks',
    'contribute_habits',
    'contribute_nutrition',
    'contribute_workouts',
    'collect_all_candidates',
]
