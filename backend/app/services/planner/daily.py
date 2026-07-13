"""TODAY facade — delegates to the Execution Engine."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.plan import DailyTask, Plan
from app.models.planner import DayBlock
from app.services.execution.service import build_today, rebuild_today, toggle_today_task


def build_daily_checklist(db: Session, plan: Plan, day: date) -> list[DailyTask]:
    _, tasks = build_today(db, plan, day)
    return tasks


def get_today_view(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    return build_today(db, plan, day)


def toggle_task(
    db: Session,
    plan: Plan,
    task: DailyTask,
    completed: bool,
    day: date,
) -> tuple[list[DayBlock], list[DailyTask]]:
    return toggle_today_task(db, plan, task, completed, day)


def rebuild_today_view(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    return rebuild_today(db, plan, day)
