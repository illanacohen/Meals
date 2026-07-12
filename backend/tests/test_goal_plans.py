def test_create_plan_with_habits_and_today_checklist(client):
    plan = client.post(
        '/plans/',
        json={
            'name': 'Definicion 12 semanas',
            'goal_type': 'deficit',
            'start_date': '2026-07-12',
            'duration_weeks': 12,
            'status': 'active',
        },
    )
    assert plan.status_code == 201
    body = plan.json()
    assert body['name'] == 'Definicion 12 semanas'
    assert body['end_date'] == '2026-10-04'
    plan_id = body['id']

    habit = client.post(
        f'/plans/{plan_id}/habits',
        json={
            'name': 'No picotear',
            'category': 'nutrition',
            'frequency': 'daily',
        },
    )
    assert habit.status_code == 201

    habit2 = client.post(
        f'/plans/{plan_id}/habits',
        json={'name': 'Caminar 10000 pasos', 'category': 'steps', 'target_value': 10000, 'target_unit': 'steps'},
    )
    assert habit2.status_code == 201

    today = client.get(f'/plans/{plan_id}/today', params={'day': '2026-07-12'})
    assert today.status_code == 200
    checklist = today.json()

    # Hygiene pack (6) + 2 habits
    assert checklist['total_count'] == 8
    assert checklist['completed_count'] == 0
    assert len(checklist['blocks']) == 3
    block_types = [b['type'] for b in checklist['blocks']]
    assert block_types == ['high_performance', 'execution', 'recovery']

    # Wake-relative windows (defaults 07:00–23:00 → 16h → 4h / 7.2h / 4.8h)
    assert checklist['blocks'][0]['starts_at'].startswith('2026-07-12T07:00')
    assert checklist['blocks'][0]['ends_at'].startswith('2026-07-12T11:00')

    titles = {t['title'] for t in checklist['tasks']}
    assert 'No picotear' in titles
    assert 'Caminar 10000 pasos' in titles
    assert 'Brush teeth' in titles
    assert 'Make bed' in titles

    # High-friction hygiene preferentially in Block 1
    hp_titles = {t['title'] for t in checklist['blocks'][0]['tasks']}
    assert 'Brush teeth' in hp_titles
    assert 'Make bed' in hp_titles

    habit_task = next(t for t in checklist['tasks'] if t['title'] == 'No picotear')
    toggled = client.patch(
        f'/plans/{plan_id}/today/{habit_task["id"]}',
        params={'day': '2026-07-12'},
        json={'completed': True},
    )
    assert toggled.status_code == 200
    assert toggled.json()['completed_count'] == 1

    progress = client.post(
        f'/plans/{plan_id}/progress',
        json={'date': '2026-07-12', 'weight_kg': 62.5, 'adherence_percent': 80},
    )
    assert progress.status_code == 201
    listed = client.get(f'/plans/{plan_id}/progress')
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_meal_plans_still_work_under_nutrition_prefix(client):
    meal_day = client.post('/meal-plans/', json={'date': '2026-08-01', 'name': 'Dia 1'})
    assert meal_day.status_code == 201
    assert len(meal_day.json()['slots']) == 4
