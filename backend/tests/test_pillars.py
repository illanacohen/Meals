def test_plan_starts_without_seeded_pillars(client):
    plan = client.post(
        '/plans/',
        json={
            'name': 'Empty Pillars',
            'goal_type': 'maintenance',
            'start_date': '2026-07-12',
            'status': 'active',
        },
    )
    assert plan.status_code == 201
    assert plan.json()['pillars'] == []
    listed = client.get(f'/plans/{plan.json()["id"]}/pillars')
    assert listed.status_code == 200
    assert listed.json() == []


def test_user_defined_pillars_crud_and_habit_link(client):
    plan = client.post(
        '/plans/',
        json={
            'name': 'Life Domains',
            'goal_type': 'custom',
            'start_date': '2026-07-12',
            'status': 'active',
        },
    )
    plan_id = plan.json()['id']

    work = client.post(
        f'/plans/{plan_id}/pillars',
        json={'name': 'Work', 'icon': 'work', 'display_order': 1},
    )
    assert work.status_code == 201
    reading = client.post(
        f'/plans/{plan_id}/pillars',
        json={'name': 'University', 'display_order': 2},
    )
    assert reading.status_code == 201
    reading_id = reading.json()['id']

    habit = client.post(
        f'/plans/{plan_id}/habits',
        json={'name': 'Read paper', 'pillar_id': reading_id},
    )
    assert habit.status_code == 201
    assert habit.json()['pillar_id'] == reading_id

    today = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-12'})
    assert today.status_code == 200
    task = next(t for t in today.json()['tasks'] if t['title'] == 'Read paper')
    assert task['pillar_id'] == reading_id
    assert task['source_module'] == 'habits'
    assert task['source_entity'] == 'habit'
    assert task['status'] == 'pending'
    assert 'priority' in task

    renamed = client.patch(
        f'/plans/{plan_id}/pillars/{reading_id}',
        json={'name': 'Learning', 'display_order': 5},
    )
    assert renamed.status_code == 200
    assert renamed.json()['name'] == 'Learning'

    deleted = client.delete(f'/plans/{plan_id}/pillars/{work.json()["id"]}')
    assert deleted.status_code == 204
    names = {p['name'] for p in client.get(f'/plans/{plan_id}/pillars').json()}
    assert names == {'Learning'}


def test_habit_rejects_foreign_pillar(client):
    a = client.post(
        '/plans/',
        json={'name': 'A', 'goal_type': 'custom', 'start_date': '2026-07-12', 'status': 'draft'},
    )
    b = client.post(
        '/plans/',
        json={'name': 'B', 'goal_type': 'custom', 'start_date': '2026-07-12', 'status': 'draft'},
    )
    pillar = client.post(
        f'/plans/{a.json()["id"]}/pillars',
        json={'name': 'Finance'},
    ).json()
    bad = client.post(
        f'/plans/{b.json()["id"]}/habits',
        json={'name': 'Budget review', 'pillar_id': pillar['id']},
    )
    assert bad.status_code == 400
