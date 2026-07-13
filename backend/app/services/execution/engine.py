"""Core Execution Engine: Plan + UserContext → TODAY projection.

Deterministic given: Plan, UserContext, current date.
TODAY (TodayTask rows) is a generated cache — not the domain source of truth.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session, joinedload

from app.models.context import UserContext
from app.models.plan import Plan, TodayTask
from app.models.planner import DayBlock, DaySchedulePolicy
from app.services.context import context_service
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext
from app.services.execution.registry import collect_candidates
from app.services.planner.schedule import BLOCK_TYPES, ensure_day_blocks, resolve_policy

BLOCK_HIGH = 'high_performance'
BLOCK_EXEC = 'execution'
BLOCK_RECOVERY = 'recovery'


def _choose_block(c: ExecutionCandidate, policy: DaySchedulePolicy) -> str:
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


def _sort_key(c: ExecutionCandidate) -> tuple:
    return (-c.priority, -c.friction, c.title)


def _upsert_key(c: ExecutionCandidate) -> tuple:
    return (c.legacy_task_type, c.source_id, c.title)


def run_execution_engine(
    db: Session,
    plan: Plan,
    day: date,
    user_context: UserContext | None = None,
) -> tuple[list[DayBlock], list[TodayTask]]:
    """
    Plan + UserContext → DayBlocks → TodayTask projection.

    Loads UserContext via ContextService when not injected. Never reads
    onboarding/profile tables directly.
    """
    plan = (
        db.query(Plan)
        .options(joinedload(Plan.habits))
        .filter(Plan.id == plan.id)
        .one()
    )
    user_context = user_context or context_service.load_for_execution(db, plan)
    policy = resolve_policy(db, plan, user_context=user_context)
    blocks = ensure_day_blocks(db, plan, day, policy)
    block_by_type = {b.block_type: b for b in blocks}

    ctx = ExecutionContext(
        delay_first_meal=policy.delay_first_meal,
        training_hour=(
            user_context.preferred_training_time
            or policy.training_hour
        ),
        user_context=user_context,
    )
    candidates = collect_candidates(db, plan, day, ctx)

    buckets: dict[str, list[ExecutionCandidate]] = {t: [] for t in BLOCK_TYPES}
    for c in candidates:
        buckets[_choose_block(c, policy)].append(c)
    for block_type in BLOCK_TYPES:
        buckets[block_type].sort(key=_sort_key)

    existing = (
        db.query(TodayTask)
        .filter(TodayTask.plan_id == plan.id, TodayTask.date == day)
        .all()
    )
    by_key = {(t.task_type, t.source_id, t.title): t for t in existing}
    seen_keys: set[tuple] = set()

    order = 0
    for block_type in BLOCK_TYPES:
        for c in buckets[block_type]:
            key = _upsert_key(c)
            seen_keys.add(key)
            task = by_key.get(key)
            block = block_by_type[block_type]
            completed = bool(c.completed)
            if task is None:
                task = TodayTask(
                    plan_id=plan.id,
                    date=day,
                    title=c.title,
                    task_type=c.legacy_task_type,
                    source_module=c.source_module,
                    source_entity=c.source_entity,
                    source_id=c.source_id,
                    plan_task_id=c.plan_task_id,
                    execution_item_id=c.execution_item_id,
                    dynamic_execution_item_id=c.dynamic_execution_item_id,
                    pillar_id=c.pillar_id,
                    priority=c.priority,
                    status='completed' if completed else 'pending',
                    block_type=block_type,
                    estimated_duration_minutes=c.duration_minutes,
                    scheduled_time=block.starts_at,
                    completed=completed,
                    order_index=order,
                )
                db.add(task)
                by_key[key] = task
            else:
                task.block_type = block_type
                task.plan_task_id = c.plan_task_id
                task.execution_item_id = c.execution_item_id
                task.dynamic_execution_item_id = c.dynamic_execution_item_id
                task.pillar_id = c.pillar_id
                task.source_module = c.source_module
                task.source_entity = c.source_entity
                task.source_id = c.source_id
                task.priority = c.priority
                task.estimated_duration_minutes = c.duration_minutes
                task.order_index = order
                # Completions / exceptions live on ExecutionLog / DynamicExecutionItem
                task.completed = completed
                task.status = 'completed' if completed else 'pending'
                if not completed:
                    task.scheduled_time = block.starts_at
            order += 1

    for key, task in list(by_key.items()):
        if key not in seen_keys and not task.completed:
            db.delete(task)

    db.commit()

    tasks = (
        db.query(TodayTask)
        .filter(TodayTask.plan_id == plan.id, TodayTask.date == day)
        .order_by(TodayTask.order_index.asc(), TodayTask.id.asc())
        .all()
    )
    blocks = (
        db.query(DayBlock)
        .filter(DayBlock.plan_id == plan.id, DayBlock.date == day)
        .all()
    )
    blocks_sorted = sorted(
        blocks,
        key=lambda b: BLOCK_TYPES.index(b.block_type) if b.block_type in BLOCK_TYPES else 99,
    )
    return blocks_sorted, tasks


# Aliases
generate_today = run_execution_engine
materialize_today = run_execution_engine
