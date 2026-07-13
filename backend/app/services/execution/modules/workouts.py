"""Workouts module contributor."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.plan import Plan, WorkoutDay, WorkoutProgram
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.registry import register_contributor

BLOCK_EXEC = 'execution'
BLOCK_RECOVERY = 'recovery'


@register_contributor('workouts')
def contribute_workouts(
    db: Session,
    plan: Plan,
    day: date,
    ctx: ExecutionContext,
) -> list[ExecutionCandidate]:
    program = (
        db.query(WorkoutProgram)
        .options(joinedload(WorkoutProgram.days))
        .filter(WorkoutProgram.plan_id == plan.id)
        .first()
    )
    if program is None:
        return []

    dow = day.weekday() + 1
    match: WorkoutDay | None = next((wd for wd in program.days if wd.day_of_week == dow), None)
    if match is None:
        return []

    preferred = BLOCK_EXEC
    if ctx.training_hour is not None and ctx.training_hour.hour >= 18:
        preferred = BLOCK_RECOVERY

    return [
        ExecutionCandidate(
            title=match.name,
            pillar_id=program.pillar_id,
            source_module='workouts',
            source_entity='workout_day',
            source_id=match.id,
            priority=5,
            friction=4,
            duration_minutes=60,
            preferred_block=preferred,
            category='training',
        )
    ]
