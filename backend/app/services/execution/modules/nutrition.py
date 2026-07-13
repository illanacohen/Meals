"""Nutrition module contributor — meal slots → execution candidates."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.meal import MealPlan
from app.models.plan import Plan
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.registry import register_contributor

BLOCK_EXEC = 'execution'
BLOCK_RECOVERY = 'recovery'


@register_contributor('nutrition')
def contribute_nutrition(
    db: Session,
    plan: Plan,
    day: date,
    ctx: ExecutionContext,
) -> list[ExecutionCandidate]:
    meal_day = (
        db.query(MealPlan)
        .options(joinedload(MealPlan.slots))
        .filter(MealPlan.date == day, MealPlan.goal_plan_id == plan.id)
        .first()
    )
    if meal_day is None:
        meal_day = (
            db.query(MealPlan)
            .options(joinedload(MealPlan.slots))
            .filter(MealPlan.date == day, MealPlan.goal_plan_id.is_(None))
            .first()
        )
    if meal_day is None:
        return []

    slots = sorted(meal_day.slots, key=lambda s: s.position)
    out: list[ExecutionCandidate] = []
    for i, slot in enumerate(slots):
        force = None
        preferred = BLOCK_EXEC
        if ctx.delay_first_meal and i == 0:
            force = BLOCK_EXEC
        elif i == len(slots) - 1:
            preferred = BLOCK_RECOVERY
        out.append(
            ExecutionCandidate(
                title=slot.label,
                pillar_id=meal_day.pillar_id,
                source_module='nutrition',
                source_entity='meal_slot',
                source_id=slot.id,
                priority=4 if i == 0 else 3,
                friction=2,
                duration_minutes=30,
                preferred_block=preferred,
                force_block=force,
                category='nutrition',
            )
        )
    return out
