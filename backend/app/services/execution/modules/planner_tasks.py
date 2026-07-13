"""Planner module — planned ExecutionItems (non-habit) for TODAY."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.execution import ExecutionCompletion, ExecutionItem
from app.models.plan import Plan
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.recurrence import matches_recurrence
from app.services.execution.registry import register_contributor
from app.services.execution.seeding import seed_plan_hygiene_execution_items


def _schedule_bits(item: ExecutionItem) -> tuple[str, int, list]:
    rule = item.schedule_rule or {}
    preferred = str(rule.get('preferred_block') or 'any')
    friction = int(rule.get('friction') or 3)
    forbidden = list(rule.get('forbidden_blocks') or [])
    return preferred, friction, forbidden


@register_contributor('planner')
def contribute_planner_tasks(
    db: Session,
    plan: Plan,
    day: date,
    ctx: ExecutionContext,
) -> list[ExecutionCandidate]:
    seed_plan_hygiene_execution_items(db, plan)

    items = (
        db.query(ExecutionItem)
        .filter(
            ExecutionItem.plan_id == plan.id,
            ExecutionItem.active.is_(True),
            ExecutionItem.source_module == 'planner',
        )
        .all()
    )
    ids = [i.id for i in items]
    completions = {
        c.execution_item_id: c
        for c in db.query(ExecutionCompletion)
        .filter(
            ExecutionCompletion.execution_item_id.in_(ids or [0]),
            ExecutionCompletion.date == day,
        )
        .all()
    }

    out: list[ExecutionCandidate] = []
    for item in items:
        if not matches_recurrence(item.recurrence_rule, day):
            continue
        preferred, friction, forbidden = _schedule_bits(item)
        meta = item.item_metadata or {}
        comp = completions.get(item.id)
        out.append(
            ExecutionCandidate(
                title=item.title,
                pillar_id=item.pillar_id,
                source_module='planner',
                source_entity='execution_item',
                source_id=item.id,
                priority=item.priority,
                friction=friction,
                duration_minutes=item.estimated_duration,
                preferred_block=preferred,
                forbidden_blocks=forbidden,
                execution_item_id=item.id,
                completed=bool(comp.completed) if comp else False,
                category=meta.get('category'),
            )
        )
    return out
