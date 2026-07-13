"""Planner module — planned ExecutionItems (non-habit) for TODAY."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from app.models.execution import ExecutionItem, ExecutionLog
from app.models.plan import Plan
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.log_semantics import log_means_completed
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
    logs = {
        log.execution_item_id: log
        for log in db.query(ExecutionLog)
        .filter(
            ExecutionLog.execution_item_id.in_(ids or [0]),
            ExecutionLog.date == day,
        )
        .all()
    }

    out: list[ExecutionCandidate] = []
    for item in items:
        if not matches_recurrence(item.recurrence_rule, day):
            continue
        preferred, friction, forbidden = _schedule_bits(item)
        meta = item.item_metadata or {}
        # Prefer schedule_rule block overrides from substituted metadata
        if meta.get('preferred_block'):
            preferred = str(meta['preferred_block'])
        if meta.get('friction') is not None:
            friction = int(meta['friction'])
        if meta.get('estimated_duration') is not None:
            duration = int(meta['estimated_duration'])
        else:
            duration = item.estimated_duration
        log = logs.get(item.id)
        out.append(
            ExecutionCandidate(
                title=item.title,
                pillar_id=item.pillar_id,
                source_module='planner',
                source_entity='execution_item',
                source_id=item.id,
                priority=item.priority,
                friction=friction,
                duration_minutes=duration,
                preferred_block=preferred,
                forbidden_blocks=forbidden,
                execution_item_id=item.id,
                completed=log_means_completed(log.status if log else None),
                category=meta.get('category'),
            )
        )
    return out
