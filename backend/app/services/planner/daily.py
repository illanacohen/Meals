"""TODAY facade — orchestrates schedule + engine."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.plan import DailyTask, HabitCompletion, Plan
from app.models.planner import DayBlock
from app.services.planner.engine import build_today_tasks, regenerate_day


def build_daily_checklist(db: Session, plan: Plan, day: date) -> list[DailyTask]:
    """Backward-compatible flat list of today's tasks."""
    _, tasks = build_today_tasks(db, plan, day)
    return tasks


def get_today_view(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    """Blocks + tasks for the home TODAY surface."""
    return build_today_tasks(db, plan, day)


def toggle_task(
    db: Session,
    plan: Plan,
    task: DailyTask,
    completed: bool,
    day: date,
) -> tuple[list[DayBlock], list[DailyTask]]:
    """UC4 — mark complete; write HabitCompletion when source is habit."""
    task.completed = completed
    if task.task_type == 'habit' and task.source_id:
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
    return get_today_view(db, plan, day)


def rebuild_today(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    return regenerate_day(db, plan, day)
