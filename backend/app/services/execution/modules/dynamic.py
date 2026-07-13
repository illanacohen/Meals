"""Dynamic (ad-hoc) life tasks — not part of the long-term Plan catalog."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.execution import DynamicExecutionItem
from app.models.plan import Plan
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.registry import register_contributor


@register_contributor('dynamic')
def contribute_dynamic(
    db: Session,
    plan: Plan,
    day: date,
    ctx: ExecutionContext,
) -> list[ExecutionCandidate]:
    due_today = (
        db.query(DynamicExecutionItem)
        .filter(
            DynamicExecutionItem.plan_id == plan.id,
            DynamicExecutionItem.due_date == day,
        )
        .all()
    )
    undated_open = (
        db.query(DynamicExecutionItem)
        .filter(
            DynamicExecutionItem.plan_id == plan.id,
            DynamicExecutionItem.due_date.is_(None),
            DynamicExecutionItem.completed.is_(False),
        )
        .all()
    )
    seen: set[int] = set()
    out: list[ExecutionCandidate] = []
    for item in list(due_today) + list(undated_open):
        if item.id in seen:
            continue
        seen.add(item.id)
        out.append(
            ExecutionCandidate(
                title=item.title,
                pillar_id=item.pillar_id,
                source_module='dynamic',
                source_entity='dynamic',
                source_id=item.id,
                priority=item.priority,
                friction=2,
                duration_minutes=20,
                preferred_block='any',
                dynamic_execution_item_id=item.id,
                completed=item.completed,
                category='dynamic',
            )
        )
    return out
