"""Wake/sleep → DayBlocks for a calendar date."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.models.planner import DayBlock, DaySchedulePolicy
from app.models.user_profile import UserProfile

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


def resolve_policy(db: Session, plan: Plan) -> DaySchedulePolicy:
    """Planner-facing schedule policy from profile (+ plan goal flags)."""
    profile: UserProfile | None = None
    if plan.user_profile_id:
        profile = db.query(UserProfile).filter(UserProfile.id == plan.user_profile_id).first()
    if profile is None:
        profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()

    policy = None
    if profile is not None:
        policy = (
            db.query(DaySchedulePolicy)
            .filter(DaySchedulePolicy.user_profile_id == profile.id)
            .first()
        )
    else:
        policy = (
            db.query(DaySchedulePolicy)
            .filter(DaySchedulePolicy.user_profile_id.is_(None))
            .first()
        )

    wake = (profile.wake_time if profile and profile.wake_time else DEFAULT_WAKE)
    sleep = (profile.sleep_time if profile and profile.sleep_time else DEFAULT_SLEEP)
    meals = profile.meals_per_day if profile else 4
    training_hour = profile.training_hour if profile else None
    delay_first = plan.goal_type == 'deficit'

    if policy is None:
        policy = DaySchedulePolicy(
            user_profile_id=profile.id if profile else None,
            wake_time=wake,
            sleep_time=sleep,
            work_pattern='variable',
            training_hour=training_hour,
            meals_per_day=meals,
            block1_ratio=DEFAULT_RATIOS[0],
            block2_ratio=DEFAULT_RATIOS[1],
            block3_ratio=DEFAULT_RATIOS[2],
            delay_first_meal=delay_first,
            timezone='UTC',
        )
        db.add(policy)
        db.flush()
    else:
        policy.wake_time = wake
        policy.sleep_time = sleep
        policy.meals_per_day = meals
        policy.training_hour = training_hour
        policy.delay_first_meal = delay_first or policy.delay_first_meal

    return policy


def ensure_day_blocks(db: Session, plan: Plan, day: date, policy: DaySchedulePolicy | None = None) -> list[DayBlock]:
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
