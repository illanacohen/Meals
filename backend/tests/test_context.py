"""UserContext aggregate + ContextService + engine wiring."""

from datetime import date, time

from app.models.context import UserContext
from app.models.plan import Plan
from app.services.context import context_service
from app.services.execution.engine import run_execution_engine
from app.services.planner.schedule import resolve_policy


def test_get_context_builds_defaults(client):
    res = client.get('/context/')
    assert res.status_code == 200
    body = res.json()
    assert body['id'] >= 1
    assert body['timezone'] == 'UTC'
    assert body['wake_time'] == '07:00:00'
    assert body['sleep_time'] == '23:00:00'


def test_patch_context(client):
    client.get('/context/')
    res = client.patch(
        '/context/',
        json={
            'age': 30,
            'sex': 'female',
            'wake_time': '06:30:00',
            'dietary_restrictions': ['vegetarian'],
            'food_intolerances': ['lactose'],
            'equipment': ['dumbbells'],
            'gym_access': False,
            'motivation_style': 'identity',
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body['age'] == 30
    assert body['sex'] == 'female'
    assert body['wake_time'] == '06:30:00'
    assert body['dietary_restrictions'] == ['vegetarian']
    assert body['food_intolerances'] == ['lactose']
    assert body['equipment'] == ['dumbbells']
    assert body['gym_access'] is False
    assert body['motivation_style'] == 'identity'


def test_onboarding_produces_user_context(client):
    onboard = client.post(
        '/onboarding/',
        json={
            'age': 28,
            'gender': 'male',
            'weight_kg': 80,
            'height_cm': 180,
            'goal': 'maintenance',
            'create_goal_for_today': False,
        },
    )
    assert onboard.status_code == 201

    ctx = client.get('/context/')
    assert ctx.status_code == 200
    body = ctx.json()
    assert body['age'] == 28
    assert body['sex'] == 'male'
    assert body['weight_kg'] == 80
    assert body['height_cm'] == 180
    assert body['user_profile_id'] is not None


def test_execution_engine_uses_user_context_wake(db_session):
    plan = Plan(
        name='Ctx Plan',
        goal_type='maintenance',
        start_date=date(2026, 7, 12),
        status='active',
    )
    db_session.add(plan)
    db_session.flush()

    ctx = UserContext(
        wake_time=time(5, 0),
        sleep_time=time(21, 0),
        timezone='America/Sao_Paulo',
    )
    db_session.add(ctx)
    db_session.commit()

    blocks, _tasks = run_execution_engine(db_session, plan, date(2026, 7, 12), user_context=ctx)
    high = next(b for b in blocks if b.block_type == 'high_performance')
    assert high.starts_at.hour == 5
    assert high.starts_at.minute == 0

    policy = resolve_policy(db_session, plan, user_context=ctx)
    assert policy.wake_time == time(5, 0)
    assert policy.timezone == 'America/Sao_Paulo'


def test_context_service_load_for_execution(db_session):
    plan = Plan(
        name='Load Ctx',
        goal_type='custom',
        start_date=date(2026, 7, 12),
        status='active',
    )
    db_session.add(plan)
    db_session.commit()

    ctx = context_service.load_for_execution(db_session, plan)
    assert ctx.id is not None
    assert ctx.wake_time is not None
    db_session.commit()
