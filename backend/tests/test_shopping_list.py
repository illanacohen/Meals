from types import SimpleNamespace

from app.services.shopping_list import build_shopping_list


def test_build_shopping_list_aggregates_and_formats():
    items = [
        SimpleNamespace(name='pollo', grams=700),
        SimpleNamespace(name='pollo', grams=700),
        SimpleNamespace(name='arroz', grams=500),
        SimpleNamespace(name='arroz', grams=300),
        SimpleNamespace(name='huevo', grams=50 * 8),
        SimpleNamespace(name='huevos', grams=50 * 4),
        SimpleNamespace(name='zapallito', grams=600),
    ]
    lines = build_shopping_list(items)
    by_name = {row['name']: row for row in lines}

    assert by_name['pollo']['display'] == '1.4 kg pollo'
    assert by_name['pollo']['unit'] == 'kg'
    assert by_name['arroz']['display'] == '800 g arroz'
    assert by_name['huevo']['display'] == '12 huevos'
    assert by_name['huevo']['quantity'] == 12
    assert by_name['zapallito']['display'] == '600 g zapallito'


def test_shopping_list_endpoint_weekly(client):
    # Day 1
    p1 = client.post('/meal-plans/', json={'date': '2026-07-13'})
    assert p1.status_code == 201
    id1 = p1.json()['id']
    r = client.post(
        f'/meal-plans/{id1}/slots/2/meals',
        json={
            'name': 'Almuerzo',
            'calories': 500,
            'protein': 40,
            'fat': 10,
            'carbs': 40,
            'fiber': 2,
            'items': [
                {'name': 'pollo', 'quantity': 700, 'unit': 'g'},
                {'name': 'arroz', 'quantity': 400, 'unit': 'g'},
                {'name': 'huevo', 'quantity': 6, 'unit': 'unit'},
            ],
        },
    )
    assert r.status_code == 201

    # Day 2
    p2 = client.post('/meal-plans/', json={'date': '2026-07-14'})
    assert p2.status_code == 201
    id2 = p2.json()['id']
    r = client.post(
        f'/meal-plans/{id2}/slots/4/meals',
        json={
            'name': 'Cena',
            'calories': 400,
            'protein': 35,
            'fat': 8,
            'carbs': 30,
            'fiber': 3,
            'items': [
                {'name': 'pollo', 'quantity': 700, 'unit': 'g'},
                {'name': 'arroz', 'quantity': 400, 'unit': 'g'},
                {'name': 'huevos', 'quantity': 6, 'unit': 'unit'},
                {'name': 'zapallito', 'quantity': 600, 'unit': 'g'},
            ],
        },
    )
    assert r.status_code == 201

    response = client.get(
        '/shopping-list/',
        params={'start_date': '2026-07-13', 'end_date': '2026-07-19'},
    )
    assert response.status_code == 200
    body = response.json()
    assert body['plan_count'] == 2
    assert '1.4 kg pollo' in body['lines']
    assert '800 g arroz' in body['lines']
    assert '12 huevos' in body['lines']
    assert '600 g zapallito' in body['lines']


def test_shopping_list_week_shortcut(client):
    plan = client.post('/meal-plans/', json={'date': '2026-07-20'})
    assert plan.status_code == 201
    plan_id = plan.json()['id']
    client.post(
        f'/meal-plans/{plan_id}/slots/1/meals',
        json={
            'name': 'Desayuno',
            'calories': 200,
            'protein': 12,
            'fat': 10,
            'carbs': 5,
            'fiber': 0,
            'items': [{'name': 'huevo', 'quantity': 2, 'unit': 'unit'}],
        },
    )
    response = client.get('/shopping-list/week', params={'week_start': '2026-07-20'})
    assert response.status_code == 200
    assert response.json()['end_date'] == '2026-07-26'
    assert '2 huevos' in response.json()['lines']


def test_shopping_list_empty_range(client):
    response = client.get(
        '/shopping-list/',
        params={'start_date': '2026-01-01', 'end_date': '2026-01-07'},
    )
    assert response.status_code == 200
    assert response.json()['plan_count'] == 0
    assert response.json()['items'] == []
