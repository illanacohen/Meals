def test_execution_engine_modules_registered(client):
    plan = client.post(
        '/plans/',
        json={
            'name': 'Exec Plan',
            'goal_type': 'custom',
            'start_date': '2026-07-12',
            'status': 'active',
        },
    )
    plan_id = plan.json()['id']
    mods = client.get(f'/plans/{plan_id}/execution/modules')
    assert mods.status_code == 200
    names = set(mods.json()['modules'])
    assert {'planner', 'habits', 'nutrition', 'workouts', 'dynamic'} <= names


def test_execution_today_matches_today(client):
    plan = client.post(
        '/plans/',
        json={
            'name': 'Exec Today',
            'goal_type': 'maintenance',
            'start_date': '2026-07-12',
            'status': 'active',
        },
    )
    plan_id = plan.json()['id']
    today = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-12'})
    execution = client.get(f'/plans/{plan_id}/execution/today', params={'day': '2026-07-12'})
    assert today.status_code == 200
    assert execution.status_code == 200
    assert today.json()['total_count'] == execution.json()['total_count']
    assert {t['title'] for t in today.json()['tasks']} == {
        t['title'] for t in execution.json()['tasks']
    }
