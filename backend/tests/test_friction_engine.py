"""Exception logs, visual substitution, and FrictionEngine."""

from datetime import date, time, timedelta

from app.models.execution import ExecutionItem, ExecutionLog
from app.models.plan import Plan
from app.services.context import context_service
from app.services.execution.friction_engine import friction_engine
from app.services.execution.substitution import substitution_service


def _create_plan(client, name='Friction Plan'):
    plan = client.post(
        '/plans/',
        json={
            'name': name,
            'goal_type': 'custom',
            'start_date': '2026-07-12',
            'status': 'active',
        },
    )
    assert plan.status_code == 201
    return plan.json()['id']


def test_execution_log_by_exception(client):
    plan_id = _create_plan(client, 'Logs')
    items = client.get(f'/plans/{plan_id}/execution-items').json()
    item_id = items[0]['id']

    created = client.post(
        f'/execution-items/{item_id}/logs',
        json={
            'date': '2026-07-12',
            'status': 'high_friction',
            'logged_at_time': '21:30:00',
            'metadata': {'note': 'Cooking at night drained me'},
        },
    )
    assert created.status_code == 201
    body = created.json()
    assert body['status'] == 'high_friction'
    assert body['logged_at_time'] == '21:30:00'
    assert body['metadata']['note'] == 'Cooking at night drained me'

    listed = client.get(f'/execution-items/{item_id}/logs')
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_silence_means_no_log(client):
    plan_id = _create_plan(client, 'Silence')
    items = client.get(f'/plans/{plan_id}/execution-items').json()
    item_id = items[0]['id']
    listed = client.get(f'/execution-items/{item_id}/logs')
    assert listed.status_code == 200
    assert listed.json() == []


def test_nutrition_visual_substitutes_and_replace(client):
    plan_id = _create_plan(client, 'Replace Meal')
    created = client.post(
        f'/plans/{plan_id}/execution-items',
        json={
            'title': 'Greek yogurt',
            'source_module': 'nutrition',
            'recurrence_rule': 'daily',
            'metadata': {'name': 'Greek yogurt', 'protein': 20, 'carbs': 15, 'fat': 5},
        },
    )
    assert created.status_code == 201
    item_id = created.json()['id']

    alts = client.get(f'/execution-items/{item_id}/alternatives')
    assert alts.status_code == 200
    options = alts.json()
    assert len(options) == 3
    assert all('id' in o and 'title' in o and 'metadata' in o for o in options)

    chosen = options[0]
    replaced = client.post(
        f'/execution-items/{item_id}/replace',
        json={'alternative_id': chosen['id']},
    )
    assert replaced.status_code == 200
    assert replaced.json()['item']['title'] == chosen['title']
    assert replaced.json()['proposal']['payload']['type'] == 'replace'
    assert replaced.json()['proposal']['status'] == 'accepted'


def test_replace_as_proposal_does_not_mutate(client):
    plan_id = _create_plan(client, 'Proposal Only')
    created = client.post(
        f'/plans/{plan_id}/execution-items',
        json={
            'title': 'Greek yogurt',
            'source_module': 'nutrition',
            'metadata': {'name': 'Greek yogurt', 'protein': 20, 'carbs': 15, 'fat': 5},
        },
    )
    item_id = created.json()['id']
    alts = client.get(f'/execution-items/{item_id}/alternatives').json()
    res = client.post(
        f'/execution-items/{item_id}/replace',
        json={'alternative_id': alts[0]['id'], 'as_proposal': True},
    )
    assert res.status_code == 200
    assert res.json()['item']['title'] == 'Greek yogurt'
    assert res.json()['proposal']['status'] == 'pending'


def test_friction_engine_creates_reschedule_proposal(db_session):
    ctx = context_service.get_or_build(db_session)
    plan = Plan(
        name='Friction Detect',
        goal_type='custom',
        start_date=date(2026, 7, 1),
        status='active',
        user_profile_id=ctx.user_profile_id,
    )
    db_session.add(plan)
    db_session.flush()

    item = ExecutionItem(
        plan_id=plan.id,
        title='Cook dinner',
        source_module='nutrition',
        schedule_rule={'preferred_time': '19:00:00', 'friction': 4},
        item_metadata={'name': 'Cook dinner', 'protein': 30, 'carbs': 40, 'fat': 10},
    )
    db_session.add(item)
    db_session.flush()

    as_of = date(2026, 7, 12)
    for offset in range(4):
        db_session.add(
            ExecutionLog(
                execution_item_id=item.id,
                date=as_of - timedelta(days=offset),
                status='shifted_schedule',
                logged_at_time=time(12, 0),
            )
        )
    db_session.commit()

    proposals = friction_engine.analyze_friction_patterns(
        db_session,
        ctx.id,
        as_of=as_of,
    )
    db_session.commit()
    assert len(proposals) >= 1
    payload = proposals[0].payload
    assert payload['type'] == 'reschedule'
    assert payload['execution_item_id'] == item.id
    assert 'suggested_time' in payload
    assert proposals[0].created_by == 'friction_engine'


def test_friction_engine_high_friction_evening(db_session):
    ctx = context_service.get_or_build(db_session)
    plan = Plan(
        name='Evening Friction',
        goal_type='custom',
        start_date=date(2026, 7, 1),
        status='active',
    )
    db_session.add(plan)
    db_session.flush()
    item = ExecutionItem(
        plan_id=plan.id,
        title='Night cooking',
        source_module='nutrition',
        schedule_rule={'preferred_time': '20:00:00'},
    )
    db_session.add(item)
    db_session.flush()

    as_of = date(2026, 7, 12)
    for offset in range(3):
        db_session.add(
            ExecutionLog(
                execution_item_id=item.id,
                date=as_of - timedelta(days=offset),
                status='high_friction',
                logged_at_time=time(21, 0),
            )
        )
    db_session.commit()

    proposals = friction_engine.analyze_friction_patterns(db_session, ctx.id, as_of=as_of)
    db_session.commit()
    assert len(proposals) == 1
    assert proposals[0].payload['type'] == 'reschedule'
    assert proposals[0].payload['suggested_time'] == '12:00:00'
    assert 'evening' in proposals[0].payload['reason'].lower()


def test_friction_analyze_endpoint(client, db_session):
    plan_id = _create_plan(client, 'API Friction')
    items = client.get(f'/plans/{plan_id}/execution-items').json()
    item_id = items[0]['id']
    as_of = date(2026, 7, 12)
    for offset in range(3):
        client.post(
            f'/execution-items/{item_id}/logs',
            json={
                'date': (as_of - timedelta(days=offset)).isoformat(),
                'status': 'skipped',
                'logged_at_time': '20:00:00',
            },
        )

    ctx = context_service.get_or_build(db_session)
    db_session.commit()
    res = client.post(
        '/execution-items/friction/analyze',
        params={'user_id': ctx.id, 'as_of': as_of.isoformat()},
    )
    assert res.status_code == 201
    assert isinstance(res.json(), list)


def test_substitution_respects_lactose(db_session):
    plan = Plan(
        name='Lactose',
        goal_type='custom',
        start_date=date(2026, 7, 12),
        status='active',
    )
    db_session.add(plan)
    db_session.flush()
    item = ExecutionItem(
        plan_id=plan.id,
        title='Greek yogurt',
        source_module='nutrition',
        item_metadata={'name': 'Greek yogurt', 'protein': 20, 'carbs': 15, 'fat': 5},
    )
    db_session.add(item)
    db_session.flush()

    ctx = context_service.get_or_build(db_session)
    ctx.food_intolerances = ['lactose']
    db_session.flush()

    options = substitution_service.get_smart_substitutes(db_session, item.id, ctx, limit=3)
    assert len(options) == 3
    assert all('dairy' not in (o.metadata.get('tags') or []) for o in options)
