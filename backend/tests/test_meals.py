def test_create_and_get_meal_with_items(client):
    payload = {
        'name': 'Huevos con zapallito',
        'calories': 320,
        'protein': 22,
        'fat': 18,
        'carbs': 12,
        'fiber': 3,
        'items': [
            {'name': 'huevo', 'quantity': 2, 'unit': 'unit'},
            {'name': 'zapallito', 'quantity': 150, 'unit': 'g'},
        ],
    }
    created = client.post('/meals/', json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body['name'] == 'Huevos con zapallito'
    assert len(body['items']) == 2
    egg = next(i for i in body['items'] if i['name'] == 'huevo')
    assert egg['grams'] == 100.0

    fetched = client.get(f"/meals/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()['id'] == body['id']


def test_meal_not_found(client):
    response = client.get('/meals/9999')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Meal not found'
