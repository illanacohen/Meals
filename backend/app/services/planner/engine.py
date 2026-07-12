"""Distribute candidates into DayBlocks → DailyTask projection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time

from sqlalchemy.orm import Session, joinedload

from app.models.meal import MealPlan
from app.models.plan import DailyTask, Plan, WorkoutDay, WorkoutProgram
from app.models.planner import DayBlock, DaySchedulePolicy, PlanTask
from app.services.planner.schedule import BLOCK_TYPES, ensure_day_blocks, resolve_policy
from app.services.planner.seeding import ensure_habit_plan_task, seed_plan_hygiene_tasks

BLOCK_HIGH = 'high_performance'
BLOCK_EXEC = 'execution'
BLOCK_RECOVERY = 'recovery'


@dataclass
class Candidate:
    title: str
    task_type: str
    source_id: int | None
    plan_task_id: int | None
    friction: int
    priority: int
    duration_minutes: int
    preferred_block: str
    forbidden_blocks: list[str]
    depends_on_plan_task_id: int | None = None
    category: str | None = None
    force_block: str | None = None


def _frequency_applies(frequency: str, day: date) -> bool:
    if frequency == 'weekdays':
        return day.weekday() < 5
    return True  # daily / custom → include for v1


def _choose_block(c: Candidate, policy: DaySchedulePolicy) -> str:
    if c.force_block and c.force_block in BLOCK_TYPES:
        return c.force_block
    preferred = c.preferred_block or 'any'
    if preferred in BLOCK_TYPES and preferred not in (c.forbidden_blocks or []):
        return preferred

    if c.category == 'recovery' or c.friction <= 1:
        chosen = BLOCK_RECOVERY
    elif c.friction >= 4:
        chosen = BLOCK_HIGH
    else:
        chosen = BLOCK_EXEC

    if chosen in (c.forbidden_blocks or []):
        for alt in BLOCK_TYPES:
            if alt not in (c.forbidden_blocks or []):
                return alt
    return chosen


def _collect_plan_task_candidates(db: Session, plan: Plan, day: date) -> list[Candidate]:
    seed_plan_hygiene_tasks(db, plan)
    for habit in plan.habits:
        if habit.is_active:
            ensure_habit_plan_task(db, plan, habit)

    tasks = (
        db.query(PlanTask)
        .options(joinedload(PlanTask.template))
        .filter(PlanTask.plan_id == plan.id, PlanTask.active.is_(True))
        .all()
    )
    out: list[Candidate] = []
    for pt in tasks:
        if not _frequency_applies(pt.frequency, day):
            continue
        task_type = 'habit' if pt.habit_id else 'custom'
        source_id = pt.habit_id if pt.habit_id else pt.id
        category = pt.template.category if pt.template else None
        forbidden = list(pt.forbidden_blocks or [])
        out.append(
            Candidate(
                title=pt.title,
                task_type=task_type,
                source_id=source_id,
                plan_task_id=pt.id,
                friction=pt.friction,
                priority=pt.priority,
                duration_minutes=pt.duration_minutes,
                preferred_block=pt.preferred_block or 'any',
                forbidden_blocks=forbidden,
                depends_on_plan_task_id=pt.depends_on_plan_task_id,
                category=category,
            )
        )
    return out


def _collect_meal_candidates(
    db: Session,
    plan: Plan,
    day: date,
    policy: DaySchedulePolicy,
) -> list[Candidate]:
    meal_day = (
        db.query(MealPlan)
        .options(joinedload(MealPlan.slots))
        .filter(MealPlan.date == day, MealPlan.goal_plan_id == plan.id)
        .first()
    )
    if meal_day is None:
        meal_day = db.query(MealPlan).options(joinedload(MealPlan.slots)).filter(MealPlan.date == day).first()
    if meal_day is None:
        return []

    slots = sorted(meal_day.slots, key=lambda s: s.position)
    out: list[Candidate] = []
    for i, slot in enumerate(slots):
        force = None
        preferred = BLOCK_EXEC
        if policy.delay_first_meal and i == 0:
            # Push first meal to end of Block 1 / start of Block 2
            preferred = BLOCK_EXEC
            force = BLOCK_EXEC
        elif i == len(slots) - 1:
            preferred = BLOCK_RECOVERY
        out.append(
            Candidate(
                title=slot.label,
                task_type='meal',
                source_id=slot.id,
                plan_task_id=None,
                friction=2,
                priority=4 if i == 0 else 3,
                duration_minutes=30,
                preferred_block=preferred,
                forbidden_blocks=[],
                force_block=force,
                category='nutrition',
            )
        )
    return out


def _collect_workout_candidates(
    db: Session,
    plan: Plan,
    day: date,
    policy: DaySchedulePolicy,
) -> list[Candidate]:
    program = (
        db.query(WorkoutProgram)
        .options(joinedload(WorkoutProgram.days))
        .filter(WorkoutProgram.plan_id == plan.id)
        .first()
    )
    if program is None:
        return []

    dow = day.weekday() + 1  # 1=Mon .. 7=Sun
    match: WorkoutDay | None = None
    for wd in program.days:
        if wd.day_of_week == dow:
            match = wd
            break
    if match is None:
        return []

    preferred = BLOCK_EXEC
    training_hour: time | None = policy.training_hour
    if training_hour is not None and training_hour.hour >= 18:
        preferred = BLOCK_RECOVERY

    return [
        Candidate(
            title=match.name,
            task_type='workout',
            source_id=match.id,
            plan_task_id=None,
            friction=4,
            priority=5,
            duration_minutes=60,
            preferred_block=preferred,
            forbidden_blocks=[],
            category='training',
        )
    ]


def _sort_key(c: Candidate) -> tuple:
    # Dependencies first implicitly via later pass; order by priority desc, friction desc
    return (-c.priority, -c.friction, c.title)


def build_today_tasks(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    """UC3 — ensure blocks, place candidates, upsert DailyTasks idempotently."""
    # Refresh habits relationship
    plan = (
        db.query(Plan)
        .options(joinedload(Plan.habits))
        .filter(Plan.id == plan.id)
        .one()
    )
    policy = resolve_policy(db, plan)
    blocks = ensure_day_blocks(db, plan, day, policy)
    block_by_type = {b.block_type: b for b in blocks}

    candidates = (
        _collect_plan_task_candidates(db, plan, day)
        + _collect_meal_candidates(db, plan, day, policy)
        + _collect_workout_candidates(db, plan, day, policy)
    )

    # Place into buckets
    buckets: dict[str, list[Candidate]] = {t: [] for t in BLOCK_TYPES}
    for c in candidates:
        block = _choose_block(c, policy)
        buckets[block].append(c)

    for block_type in BLOCK_TYPES:
        buckets[block_type].sort(key=_sort_key)

    existing = (
        db.query(DailyTask)
        .filter(DailyTask.plan_id == plan.id, DailyTask.date == day)
        .all()
    )
    by_key = {(t.task_type, t.source_id, t.title): t for t in existing}
    seen_keys: set[tuple] = set()

    order = 0
    for block_type in BLOCK_TYPES:
        for c in buckets[block_type]:
            key = (c.task_type, c.source_id, c.title)
            seen_keys.add(key)
            task = by_key.get(key)
            block = block_by_type[block_type]
            if task is None:
                task = DailyTask(
                    plan_id=plan.id,
                    date=day,
                    title=c.title,
                    task_type=c.task_type,
                    source_id=c.source_id,
                    plan_task_id=c.plan_task_id,
                    block_type=block_type,
                    estimated_duration_minutes=c.duration_minutes,
                    scheduled_time=block.starts_at,
                    completed=False,
                    order_index=order,
                )
                db.add(task)
                by_key[key] = task
            else:
                # Keep completed sticky; refresh placement metadata
                task.block_type = block_type
                task.plan_task_id = c.plan_task_id
                task.estimated_duration_minutes = c.duration_minutes
                task.order_index = order
                if not task.completed:
                    task.scheduled_time = block.starts_at
            order += 1

    # Remove incomplete tasks that are no longer candidates (keep completed sticky)
    for key, task in list(by_key.items()):
        if key not in seen_keys and not task.completed:
            db.delete(task)

    db.commit()

    tasks = (
        db.query(DailyTask)
        .filter(DailyTask.plan_id == plan.id, DailyTask.date == day)
        .order_by(DailyTask.order_index.asc(), DailyTask.id.asc())
        .all()
    )
    blocks = (
        db.query(DayBlock)
        .filter(DayBlock.plan_id == plan.id, DayBlock.date == day)
        .all()
    )
    blocks_sorted = sorted(blocks, key=lambda b: BLOCK_TYPES.index(b.block_type) if b.block_type in BLOCK_TYPES else 99)
    return blocks_sorted, tasks


def regenerate_day(db: Session, plan: Plan, day: date) -> tuple[list[DayBlock], list[DailyTask]]:
    """UC5 — recompute blocks and redistribute incomplete tasks."""
    return build_today_tasks(db, plan, day)
