"""Plan-centric execution domain tests."""


def _create_plan(client, name='Exec Domain'):
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


def test_execution_items_seeded_on_plan_create(client):
    plan_id = _create_plan(client)
    items = client.get(f'/plans/{plan_id}/execution-items')
    assert items.status_code == 200
    titles = {i['title'] for i in items.json()}
    assert 'Brush teeth' in titles
    assert 'Make bed' in titles
    assert all(i['source_module'] == 'planner' for i in items.json())


def test_today_is_projection_of_execution_items(client):
    plan_id = _create_plan(client, 'Projection')
    # Long-lived item survives across days without recreating a daily plan
    created = client.post(
        f'/plans/{plan_id}/execution-items',
        json={
            'title': 'Train legs',
            'recurrence_rule': 'daily',
            'priority': 5,
            'schedule_rule': {'preferred_block': 'high_performance', 'friction': 4},
            'estimated_duration': 45,
        },
    )
    assert created.status_code == 201
    item_id = created.json()['id']

    day1 = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-12'})
    day2 = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-13'})
    assert day1.status_code == 200 and day2.status_code == 200
    assert 'Train legs' in {t['title'] for t in day1.json()['tasks']}
    assert 'Train legs' in {t['title'] for t in day2.json()['tasks']}

    # Same ExecutionItem backs both projections
    task = next(t for t in day1.json()['tasks'] if t['title'] == 'Train legs')
    assert task['execution_item_id'] == item_id


def test_dynamic_items_merge_into_today(client):
    plan_id = _create_plan(client, 'Dynamic')
    dyn = client.post(
        f'/plans/{plan_id}/dynamic-items',
        json={
            'title': 'Go to the bank',
            'due_date': '2026-07-12',
            'priority': 4,
        },
    )
    assert dyn.status_code == 201
    today = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-12'})
    assert today.status_code == 200
    titles = {t['title'] for t in today.json()['tasks']}
    assert 'Go to the bank' in titles
    bank = next(t for t in today.json()['tasks'] if t['title'] == 'Go to the bank')
    assert bank['source_module'] == 'dynamic'
    assert bank['dynamic_execution_item_id'] == dyn.json()['id']

    toggled = client.patch(
        f'/plans/{plan_id}/today/{bank["id"]}',
        params={'day': '2026-07-12'},
        json={'completed': True},
    )
    assert toggled.status_code == 200
    listed = client.get(f'/plans/{plan_id}/dynamic-items')
    assert next(i for i in listed.json() if i['id'] == dyn.json()['id'])['completed'] is True


def test_plan_proposal_does_not_mutate_plan(client):
    plan_id = _create_plan(client, 'Proposals')
    before = client.get(f'/plans/{plan_id}/execution-items').json()
    prop = client.post(
        f'/plans/{plan_id}/proposals',
        json={
            'rationale': 'User skipped last three Mondays',
            'payload': {'move': {'from': 'Monday', 'to': 'Tuesday', 'title': 'Workout'}},
            'created_by': 'ai',
        },
    )
    assert prop.status_code == 201
    assert prop.json()['status'] == 'pending'

    accepted = client.patch(
        f'/plans/{plan_id}/proposals/{prop.json()["id"]}',
        json={'status': 'accepted'},
    )
    assert accepted.status_code == 200
    assert accepted.json()['status'] == 'accepted'

    after = client.get(f'/plans/{plan_id}/execution-items').json()
    assert {i['id'] for i in before} == {i['id'] for i in after}
