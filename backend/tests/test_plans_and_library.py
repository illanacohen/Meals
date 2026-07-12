def test_plan_goal_and_validate(client):
    goal = client.post(
        '/goals/',
        json={
            'date': '2026-07-10',
            'calories': 2000,
            'protein': 150,
            'fat': 60,
            'carbs': 200,
            'fiber': 30,
        },
    )
    assert goal.status_code == 201

    plan = client.post('/meal-plans/', json={'date': '2026-07-10', 'name': 'Dia test'})
    assert plan.status_code == 201
    plan_id = plan.json()['id']
    assert len(plan.json()['slots']) == 4

    meal = client.post(
        f'/meal-plans/{plan_id}/slots/2/meals',
        json={
            'name': 'Almuerzo',
            'calories': 2000,
            'protein': 150,
            'fat': 60,
            'carbs': 200,
            'fiber': 30,
            'items': [{'name': 'pollo', 'quantity': 200, 'unit': 'g'}],
        },
    )
    assert meal.status_code == 201

    validation = client.get(f'/meal-plans/{plan_id}/validate')
    assert validation.status_code == 200
    assert validation.json()['is_valid'] is True


def test_library_one_click_add_to_plan(client):
    template = client.post(
        '/library/',
        json={
            'name': 'Pollo + batata',
            'calories': 500,
            'protein': 40,
            'fat': 10,
            'carbs': 45,
            'fiber': 6,
            'items': [
                {'name': 'pollo', 'quantity': 150, 'unit': 'g'},
                {'name': 'papa', 'quantity': 200, 'unit': 'g'},
            ],
        },
    )
    assert template.status_code == 201
    template_id = template.json()['id']

    plan = client.post('/meal-plans/', json={'date': '2026-07-11'})
    assert plan.status_code == 201
    plan_id = plan.json()['id']

    applied = client.post(f'/meal-plans/{plan_id}/slots/1/from-library/{template_id}')
    assert applied.status_code == 201
    body = applied.json()
    assert body['name'] == 'Pollo + batata'
    assert len(body['items']) == 2
