"""Execution Engine public facade."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.execution import DynamicExecutionItem, ExecutionCompletion, ExecutionItem
from app.models.plan import HabitCompletion, Plan, TodayTask
from app.models.planner import DayBlock
from app.services.execution.engine import run_execution_engine
from app.services.execution.registry import list_contributors


def build_today(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[TodayTask]]:
    """Materialize TODAY via the Execution Engine (Plan + UserContext + date)."""
    return run_execution_engine(db, plan, day)


def rebuild_today(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[TodayTask]]:
    return run_execution_engine(db, plan, day)


def toggle_today_task(
    db: Session,
    plan: Plan,
    task: TodayTask,
    completed: bool,
    day: date,
) -> tuple[list[DayBlock], list[TodayTask]]:
    """Toggle a TODAY projection row; persist completion on Plan-domain entities."""
    task.completed = completed
    task.status = 'completed' if completed else 'pending'

    if task.execution_item_id:
        ei = db.get(ExecutionItem, task.execution_item_id)
        if ei:
            row = (
                db.query(ExecutionCompletion)
                .filter(
                    ExecutionCompletion.execution_item_id == ei.id,
                    ExecutionCompletion.date == day,
                )
                .first()
            )
            if row is None:
                db.add(
                    ExecutionCompletion(
                        execution_item_id=ei.id,
                        date=day,
                        completed=completed,
                    )
                )
            else:
                row.completed = completed

            if ei.habit_id:
                hc = (
                    db.query(HabitCompletion)
                    .filter(
                        HabitCompletion.habit_id == ei.habit_id,
                        HabitCompletion.date == day,
                    )
                    .first()
                )
                if hc is None:
                    db.add(
                        HabitCompletion(
                            habit_id=ei.habit_id,
                            date=day,
                            completed=completed,
                        )
                    )
                else:
                    hc.completed = completed

    if task.dynamic_execution_item_id:
        dyn = db.get(DynamicExecutionItem, task.dynamic_execution_item_id)
        if dyn:
            dyn.completed = completed

    # Legacy habit path (pre-ExecutionItem projections)
    is_habit = (
        task.source_module == 'habits'
        or task.source_entity == 'habit'
        or task.task_type == 'habit'
    )
    if is_habit and task.source_id and not task.execution_item_id:
        existing = (
            db.query(HabitCompletion)
            .filter(HabitCompletion.habit_id == task.source_id, HabitCompletion.date == day)
            .first()
        )
        if existing:
            existing.completed = completed
        else:
            db.add(
                HabitCompletion(
                    habit_id=task.source_id,
                    date=day,
                    completed=completed,
                )
            )

    db.commit()
    return build_today(db, plan, day)


def registered_modules() -> list[str]:
    return list_contributors()
