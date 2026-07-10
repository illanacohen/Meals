from app.services.meal_generator import generate_meal_for_remaining
from app.services.food_catalog import macros_for_grams


def test_generate_meal_for_remaining_macros():
    remaining = {
        'calories': 42 * 4 + 18 * 9 + 30 * 4,
        'protein': 42,
        'fat': 18,
        'carbs': 30,
        'fiber': 0,
    }
    result = generate_meal_for_remaining(
        remaining,
        meal_name='Cena',
        preferred_foods=['pollo', 'arroz', 'nueces'],
        excluded_foods=[],
        templates=[],
        slot_position=4,
    )
    assert result['name'] == 'Cena'
    assert result['source'] == 'generated'
    assert len(result['items']) >= 2
    assert result['macros']['protein'] > 0
    assert result['macros']['protein'] <= remaining['protein'] * 1.2
    assert result['remaining_before']['protein'] == 42


def test_suggest_meal_endpoint_explicit_remaining(client):
    response = client.post(
        '/suggest/meal',
        json={
            'prompt': 'Generame una cena.',
            'remaining': {'protein': 42, 'fat': 18, 'carbs': 30},
            'preferred_foods': ['pollo', 'arroz', 'zapallito'],
            'slot_position': 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['prompt'] == 'Generame una cena.'
    assert body['name'] == 'Cena'
    assert len(body['items']) >= 1
    assert body['macros']['protein'] > 0
    assert body['remaining_before']['protein'] == 42
    assert body['source'] in ('generated', 'library')


def test_suggest_meal_from_plan_and_save(client):
    goal = client.post(
        '/goals/',
        json={
            'date': '2026-07-12',
            'calories': 2000,
            'protein': 150,
            'fat': 60,
            'carbs': 200,
            'fiber': 30,
        },
    )
    assert goal.status_code == 201

    plan = client.post('/plans/', json={'date': '2026-07-12'})
    assert plan.status_code == 201
    plan_id = plan.json()['id']

    # Eat most of the day; leave ~42P / 18F / 30C for dinner
    lunch = client.post(
        f'/plans/{plan_id}/slots/2/meals',
        json={
            'name': 'Almuerzo grande',
            'calories': 2000 - (42 * 4 + 18 * 9 + 30 * 4),
            'protein': 108,
            'fat': 42,
            'carbs': 170,
            'fiber': 20,
            'items': [{'name': 'pollo', 'quantity': 300, 'unit': 'g'}],
        },
    )
    assert lunch.status_code == 201

    template = client.post(
        '/library/',
        json={
            'name': 'Cena pollo arroz',
            'calories': 450,
            'protein': 40,
            'fat': 12,
            'carbs': 35,
            'fiber': 4,
            'items': [
                {'name': 'pollo', 'quantity': 130, 'unit': 'g'},
                {'name': 'arroz', 'quantity': 100, 'unit': 'g'},
            ],
        },
    )
    assert template.status_code == 201

    response = client.post(
        '/suggest/meal',
        json={
            'prompt': 'Generame una cena.',
            'plan_id': plan_id,
            'slot_position': 4,
            'save_to_slot': True,
            'use_library': True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body['remaining_before']['protein'] == 42
    assert body['saved_meal'] is not None
    assert body['saved_meal']['slot_id'] is not None
    assert len(body['items']) >= 1


def test_suggest_meal_requires_remaining_or_plan(client):
    response = client.post('/suggest/meal', json={'prompt': 'Generame una cena.'})
    assert response.status_code == 422


def test_macros_for_grams_pollo():
    macros = macros_for_grams('pollo', 100)
    assert macros['protein'] == 31
    assert macros['calories'] == 165
