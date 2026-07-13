"""Wake/sleep → DayBlocks for a calendar date.

Schedule inputs come from UserContext (canonical). DaySchedulePolicy remains
the persisted planner policy row used to materialize block ratios.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.context import UserContext
from app.models.plan import Plan
from app.models.planner import DayBlock, DaySchedulePolicy

BLOCK_TYPES = ('high_performance', 'execution', 'recovery')
DEFAULT_WAKE = time(7, 0)
DEFAULT_SLEEP = time(23, 0)
DEFAULT_RATIOS = (0.25, 0.45, 0.30)


def waking_window(wake: time, sleep: time, day: date) -> tuple[datetime, datetime]:
    """Return absolute wake/sleep datetimes; sleep after midnight if overnight."""
    starts = datetime.combine(day, wake)
    ends = datetime.combine(day, sleep)
    if ends <= starts:
        ends += timedelta(days=1)
    return starts, ends


def resolve_policy(
    db: Session,
    plan: Plan,
    user_context: UserContext | None = None,
) -> DaySchedulePolicy:
    """
    Planner-facing schedule policy from UserContext (+ plan goal flags).

    Does not read UserProfile. When user_context is omitted, loads it via
    ContextService so callers outside the engine stay consistent.
    """
    if user_context is None:
        from app.services.context import context_service

        user_context = context_service.load_for_execution(db, plan)

    policy = None
    if user_context.user_profile_id is not None:
        policy = (
            db.query(DaySchedulePolicy)
            .filter(DaySchedulePolicy.user_profile_id == user_context.user_profile_id)
            .first()
        )
    if policy is None:
        policy = (
            db.query(DaySchedulePolicy)
            .filter(DaySchedulePolicy.user_profile_id.is_(None))
            .first()
        )

    wake = user_context.wake_time or DEFAULT_WAKE
    sleep = user_context.sleep_time or DEFAULT_SLEEP
    prefs = user_context.preferences or {}
    meals = int(prefs.get('meals_per_day') or 4)
    training_hour = user_context.preferred_training_time
    delay_first = plan.goal_type == 'deficit'
    timezone = user_context.timezone or 'UTC'

    work_pattern = 'variable'
    work_start = None
    work_end = None
    if isinstance(user_context.working_hours, dict):
        work_pattern = user_context.working_hours.get('pattern') or 'variable'
        start_raw = user_context.working_hours.get('start')
        end_raw = user_context.working_hours.get('end')
        if start_raw:
            work_start = time.fromisoformat(start_raw) if isinstance(start_raw, str) else start_raw
        if end_raw:
            work_end = time.fromisoformat(end_raw) if isinstance(end_raw, str) else end_raw

    if policy is None:
        policy = DaySchedulePolicy(
            user_profile_id=user_context.user_profile_id,
            wake_time=wake,
            sleep_time=sleep,
            work_pattern=work_pattern,
            work_start=work_start,
            work_end=work_end,
            training_hour=training_hour,
            meals_per_day=meals,
            block1_ratio=DEFAULT_RATIOS[0],
            block2_ratio=DEFAULT_RATIOS[1],
            block3_ratio=DEFAULT_RATIOS[2],
            delay_first_meal=delay_first,
            timezone=timezone,
        )
        db.add(policy)
        db.flush()
    else:
        policy.wake_time = wake
        policy.sleep_time = sleep
        policy.meals_per_day = meals
        policy.training_hour = training_hour
        policy.delay_first_meal = delay_first or policy.delay_first_meal
        policy.timezone = timezone
        policy.work_pattern = work_pattern
        if work_start is not None:
            policy.work_start = work_start
        if work_end is not None:
            policy.work_end = work_end

    return policy


def ensure_day_blocks(
    db: Session,
    plan: Plan,
    day: date,
    policy: DaySchedulePolicy | None = None,
) -> list[DayBlock]:
    """Compute and persist the three DayBlocks for plan+date (idempotent)."""
    policy = policy or resolve_policy(db, plan)
    wake_start, sleep_end = waking_window(policy.wake_time, policy.sleep_time, day)
    total = (sleep_end - wake_start).total_seconds()
    r1 = policy.block1_ratio or DEFAULT_RATIOS[0]
    r2 = policy.block2_ratio or DEFAULT_RATIOS[1]
    r3 = policy.block3_ratio or DEFAULT_RATIOS[2]
    # Normalize if slightly off
    s = r1 + r2 + r3
    if abs(s - 1.0) > 1e-6:
        r1, r2, r3 = r1 / s, r2 / s, r3 / s

    boundaries = [
        wake_start,
        wake_start + timedelta(seconds=total * r1),
        wake_start + timedelta(seconds=total * (r1 + r2)),
        sleep_end,
    ]

    existing = {
        b.block_type: b
        for b in db.query(DayBlock)
        .filter(DayBlock.plan_id == plan.id, DayBlock.date == day)
        .all()
    }

    blocks: list[DayBlock] = []
    for i, block_type in enumerate(BLOCK_TYPES):
        starts_at, ends_at = boundaries[i], boundaries[i + 1]
        block = existing.get(block_type)
        if block is None:
            block = DayBlock(
                plan_id=plan.id,
                date=day,
                block_type=block_type,
                starts_at=starts_at,
                ends_at=ends_at,
            )
            db.add(block)
        else:
            block.starts_at = starts_at
            block.ends_at = ends_at
        blocks.append(block)

    db.flush()
    return blocks
