"""Seed TaskTemplates and PlanTasks (hygiene pack + onboarding hooks)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.plan import Habit, Plan
from app.models.planner import PlanTask, TaskTemplate

# System hygiene starter pack — preferential Block 1 (high_performance)
HYGIENE_PACK: list[dict] = [
    {
        'code': 'personal_hygiene',
        'title': 'Personal hygiene',
        'category': 'hygiene',
        'default_friction': 4,
        'default_priority': 5,
        'default_duration_minutes': 10,
        'default_block_preference': 'high_performance',
    },
    {
        'code': 'brush_teeth',
        'title': 'Brush teeth',
        'category': 'hygiene',
        'default_friction': 4,
        'default_priority': 5,
        'default_duration_minutes': 3,
        'default_block_preference': 'high_performance',
    },
    {
        'code': 'make_bed',
        'title': 'Make bed',
        'category': 'hygiene',
        'default_friction': 4,
        'default_priority': 4,
        'default_duration_minutes': 3,
        'default_block_preference': 'high_performance',
    },
    {
        'code': 'hydrate',
        'title': 'Hydrate',
        'category': 'health',
        'default_friction': 3,
        'default_priority': 4,
        'default_duration_minutes': 2,
        'default_block_preference': 'high_performance',
    },
    {
        'code': 'daylight',
        'title': 'Daylight exposure',
        'category': 'health',
        'default_friction': 4,
        'default_priority': 5,
        'default_duration_minutes': 10,
        'default_block_preference': 'high_performance',
    },
    {
        'code': 'short_walk',
        'title': 'Short walk',
        'category': 'health',
        'default_friction': 3,
        'default_priority': 3,
        'default_duration_minutes': 15,
        'default_block_preference': 'high_performance',
    },
]

DIFFICULTY_FRICTION = {'easy': 2, 'medium': 3, 'hard': 4}


def ensure_system_templates(db: Session) -> list[TaskTemplate]:
    """Upsert hygiene/system TaskTemplates by code."""
    templates: list[TaskTemplate] = []
    for spec in HYGIENE_PACK:
        row = db.query(TaskTemplate).filter(TaskTemplate.code == spec['code']).first()
        if row is None:
            row = TaskTemplate(is_system=True, **spec)
            db.add(row)
        else:
            for key, value in spec.items():
                setattr(row, key, value)
            row.is_system = True
        templates.append(row)
    db.flush()
    return templates


def seed_plan_hygiene_tasks(db: Session, plan: Plan) -> list[PlanTask]:
    """Assign system hygiene pack as PlanTasks (idempotent by template)."""
    templates = ensure_system_templates(db)
    existing = {
        pt.template_id: pt
        for pt in db.query(PlanTask).filter(PlanTask.plan_id == plan.id).all()
        if pt.template_id is not None
    }
    created: list[PlanTask] = []
    for tmpl in templates:
        if tmpl.id in existing:
            continue
        pt = PlanTask(
            plan_id=plan.id,
            template_id=tmpl.id,
            pillar_id=None,
            title=tmpl.title,
            friction=tmpl.default_friction,
            priority=tmpl.default_priority,
            duration_minutes=tmpl.default_duration_minutes,
            frequency='daily',
            preferred_block=tmpl.default_block_preference,
            active=True,
        )
        db.add(pt)
        created.append(pt)
    db.flush()
    return created


def ensure_habit_plan_task(db: Session, plan: Plan, habit: Habit) -> PlanTask:
    """Ensure an active PlanTask wraps a Habit."""
    existing = (
        db.query(PlanTask)
        .filter(PlanTask.plan_id == plan.id, PlanTask.habit_id == habit.id)
        .first()
    )
    if existing:
        existing.title = habit.name
        existing.active = habit.is_active
        existing.pillar_id = habit.pillar_id
        return existing

    friction = DIFFICULTY_FRICTION.get((habit.difficulty or 'medium').lower(), 3)
    preferred = 'any'
    if habit.time_of_day == 'morning':
        preferred = 'high_performance'
    elif habit.time_of_day == 'evening':
        preferred = 'recovery'
    elif habit.time_of_day == 'afternoon':
        preferred = 'execution'

    pt = PlanTask(
        plan_id=plan.id,
        habit_id=habit.id,
        pillar_id=habit.pillar_id,
        title=habit.name,
        friction=friction,
        priority=3,
        duration_minutes=10,
        frequency=habit.frequency if habit.frequency in ('daily', 'weekdays') else 'daily',
        preferred_block=preferred,
        active=habit.is_active,
    )
    db.add(pt)
    db.flush()
    return pt
