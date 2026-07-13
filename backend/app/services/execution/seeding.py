"""Seed and sync long-lived ExecutionItems on a Plan."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.execution import ExecutionItem
from app.models.plan import Habit, Plan
from app.services.planner.seeding import DIFFICULTY_FRICTION, HYGIENE_PACK, ensure_system_templates


def seed_plan_hygiene_execution_items(db: Session, plan: Plan) -> list[ExecutionItem]:
    """Idempotent hygiene ExecutionItems from system templates."""
    templates = ensure_system_templates(db)
    existing = {
        (ei.item_metadata or {}).get('template_code'): ei
        for ei in db.query(ExecutionItem)
        .filter(
            ExecutionItem.plan_id == plan.id,
            ExecutionItem.source_module == 'planner',
        )
        .all()
        if (ei.item_metadata or {}).get('template_code')
    }
    created: list[ExecutionItem] = []
    for tmpl in templates:
        if tmpl.code in existing:
            continue
        pack = next((p for p in HYGIENE_PACK if p['code'] == tmpl.code), None)
        preferred = (pack or {}).get('default_block_preference', tmpl.default_block_preference)
        ei = ExecutionItem(
            plan_id=plan.id,
            pillar_id=None,
            source_module='planner',
            title=tmpl.title,
            description=tmpl.description,
            recurrence_rule='daily',
            schedule_rule={
                'preferred_block': preferred,
                'friction': tmpl.default_friction,
            },
            priority=tmpl.default_priority,
            estimated_duration=tmpl.default_duration_minutes,
            active=True,
            item_metadata={'template_code': tmpl.code, 'category': tmpl.category},
        )
        db.add(ei)
        created.append(ei)
    db.flush()
    return created


def ensure_habit_execution_item(db: Session, plan: Plan, habit: Habit) -> ExecutionItem:
    """Ensure a Plan-scoped ExecutionItem for a Habit."""
    existing = (
        db.query(ExecutionItem)
        .filter(ExecutionItem.plan_id == plan.id, ExecutionItem.habit_id == habit.id)
        .first()
    )
    preferred = 'any'
    if habit.time_of_day == 'morning':
        preferred = 'high_performance'
    elif habit.time_of_day == 'evening':
        preferred = 'recovery'
    elif habit.time_of_day == 'afternoon':
        preferred = 'execution'
    friction = DIFFICULTY_FRICTION.get((habit.difficulty or 'medium').lower(), 3)
    recurrence = habit.frequency if habit.frequency in ('daily', 'weekdays') else 'daily'

    if existing:
        existing.title = habit.name
        existing.active = habit.is_active
        existing.pillar_id = habit.pillar_id
        existing.recurrence_rule = recurrence
        existing.schedule_rule = {'preferred_block': preferred, 'friction': friction}
        return existing

    ei = ExecutionItem(
        plan_id=plan.id,
        pillar_id=habit.pillar_id,
        source_module='habits',
        title=habit.name,
        recurrence_rule=recurrence,
        schedule_rule={'preferred_block': preferred, 'friction': friction},
        priority=3,
        estimated_duration=10,
        active=habit.is_active,
        habit_id=habit.id,
        item_metadata={'category': habit.category},
    )
    db.add(ei)
    db.flush()
    return ei


def migrate_plan_tasks_to_execution_items(db: Session, plan: Plan) -> list[ExecutionItem]:
    """One-shot helper: copy legacy PlanTasks into ExecutionItems (idempotent)."""
    from app.models.planner import PlanTask

    created: list[ExecutionItem] = []
    tasks = db.query(PlanTask).filter(PlanTask.plan_id == plan.id, PlanTask.active.is_(True)).all()
    for pt in tasks:
        if pt.habit_id:
            habit = next((h for h in plan.habits if h.id == pt.habit_id), None)
            if habit:
                created.append(ensure_habit_execution_item(db, plan, habit))
            continue
        template_code = pt.template.code if pt.template else None
        if template_code:
            existing = (
                db.query(ExecutionItem)
                .filter(
                    ExecutionItem.plan_id == plan.id,
                    ExecutionItem.source_module == 'planner',
                )
                .all()
            )
            if any((e.item_metadata or {}).get('template_code') == template_code for e in existing):
                continue
        else:
            dup = (
                db.query(ExecutionItem)
                .filter(
                    ExecutionItem.plan_id == plan.id,
                    ExecutionItem.title == pt.title,
                    ExecutionItem.source_module == 'planner',
                )
                .first()
            )
            if dup:
                continue
        ei = ExecutionItem(
            plan_id=plan.id,
            pillar_id=pt.pillar_id,
            source_module='planner',
            title=pt.title,
            recurrence_rule=pt.frequency if pt.frequency in ('daily', 'weekdays') else 'daily',
            schedule_rule={
                'preferred_block': pt.preferred_block or 'any',
                'friction': pt.friction,
                'forbidden_blocks': list(pt.forbidden_blocks or []),
            },
            priority=pt.priority,
            estimated_duration=pt.duration_minutes,
            active=pt.active,
            item_metadata={'template_code': template_code, 'legacy_plan_task_id': pt.id},
        )
        db.add(ei)
        created.append(ei)
    db.flush()
    return created
