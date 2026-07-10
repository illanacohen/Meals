def test_onboarding_basics_then_refine_schedule(client):
    basics = client.post(
        '/onboarding/',
        json={
            'age': 28,
            'gender': 'male',
            'weight_kg': 80,
            'height_cm': 178,
            'goal': 'deficit',
            'create_goal_for_today': False,
        },
    )
    assert basics.status_code == 201
    body = basics.json()
    assert body['targets']['calories'] > 0
    assert body['profile']['gender'] == 'male'

    refined = client.patch(
        '/onboarding/refine',
        json={
            'training_hour': '14:00:00',
            'training_type': 'strength',
            'create_goal_for_today': False,
        },
    )
    assert refined.status_code == 200
    dist = {d['label']: d['focus'] for d in refined.json()['distribution']}
    assert dist['Desayuno'] == 'Proteina + grasa'
    assert dist['Almuerzo'] == 'Muchos carbohidratos'
    assert dist['Merienda'] == 'Recuperacion'
    assert dist['Cena'] == 'Completar macros'
