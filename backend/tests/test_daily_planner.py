"""Unit tests for Daily Planner schedule + engine placement."""

from datetime import date, time

from app.models.plan import Plan
from app.services.planner.schedule import ensure_day_blocks, resolve_policy, waking_window
from app.services.planner.seeding import HYGIENE_PACK, ensure_system_templates, seed_plan_hygiene_tasks


def test_waking_window_same_day():
    start, end = waking_window(time(7, 0), time(23, 0), date(2026, 7, 12))
    assert (end - start).total_seconds() == 16 * 3600


def test_waking_window_overnight():
    start, end = waking_window(time(22, 0), time(6, 0), date(2026, 7, 12))
    assert end.day == 13
    assert (end - start).total_seconds() == 8 * 3600


def test_day_blocks_default_ratios(db_session):
    plan = Plan(
        name='Test',
        goal_type='deficit',
        start_date=date(2026, 7, 12),
        status='active',
    )
    db_session.add(plan)
    db_session.flush()

    policy = resolve_policy(db_session, plan)
    assert policy.block1_ratio == 0.25
    assert policy.delay_first_meal is True

    blocks = ensure_day_blocks(db_session, plan, date(2026, 7, 12), policy)
    db_session.commit()
    assert [b.block_type for b in blocks] == [
        'high_performance',
        'execution',
        'recovery',
    ]
    # 07:00–11:00 / 11:00–18:12 / 18:12–23:00
    assert blocks[0].starts_at.hour == 7
    assert blocks[0].ends_at.hour == 11
    assert blocks[1].starts_at.hour == 11
    assert blocks[2].ends_at.hour == 23


def test_hygiene_seed_idempotent(db_session):
    plan = Plan(
        name='Seed',
        goal_type='maintenance',
        start_date=date(2026, 7, 12),
        status='active',
    )
    db_session.add(plan)
    db_session.flush()

    ensure_system_templates(db_session)
    first = seed_plan_hygiene_tasks(db_session, plan)
    second = seed_plan_hygiene_tasks(db_session, plan)
    db_session.commit()

    assert len(first) == len(HYGIENE_PACK)
    assert second == []
