from app.services.food_catalog import resolve_item_grams, FoodResolutionError
from app.services.macro_engine import validate_plan_against_goal
from app.services.onboarding_engine import distribute_macros
from datetime import time
from types import SimpleNamespace


def test_resolve_egg_units_to_grams():
    assert resolve_item_grams('huevo', 2, 'unit') == 100.0


def test_resolve_grams_passthrough():
    assert resolve_item_grams('pollo', 150, 'g') == 150.0


def test_resolve_unknown_unit_food_requires_grams_per_unit():
    try:
        resolve_item_grams('alimento-raro', 1, 'unit')
        assert False, 'expected FoodResolutionError'
    except FoodResolutionError:
        pass

    assert resolve_item_grams('alimento-raro', 1, 'unit', grams_per_unit=75) == 75.0


def test_validate_plan_within_tolerance():
    goal = SimpleNamespace(calories=2000, protein=150, fat=60, carbs=200, fiber=30)
    totals = {'calories': 2050, 'protein': 148, 'fat': 58, 'carbs': 195, 'fiber': 29}
    result = validate_plan_against_goal(goal, totals, tolerance_percent=5)
    assert result['is_valid'] is True


def test_validate_plan_over_calories():
    goal = SimpleNamespace(calories=2000, protein=150, fat=60, carbs=200, fiber=30)
    totals = {'calories': 2500, 'protein': 150, 'fat': 60, 'carbs': 200, 'fiber': 30}
    result = validate_plan_against_goal(goal, totals, tolerance_percent=5)
    assert result['is_valid'] is False
    assert any(m['nutrient'] == 'calories' and m['status'] == 'over' for m in result['macros'])


def test_distribution_after_lunch_roles():
    targets = {'calories': 2000, 'protein': 150, 'fat': 60, 'carbs': 200, 'fiber': 30}
    dist = distribute_macros(targets, training_time=None, training_hour=time(14, 0))
    by_label = {d['label']: d['focus'] for d in dist}
    assert by_label['Desayuno'] == 'Proteina + grasa'
    assert by_label['Almuerzo'] == 'Muchos carbohidratos'
    assert by_label['Merienda'] == 'Recuperacion'
    assert by_label['Cena'] == 'Completar macros'


def test_distribution_evening_6pm_roles():
    targets = {'calories': 2000, 'protein': 150, 'fat': 60, 'carbs': 200, 'fiber': 30}
    dist = distribute_macros(targets, training_time=None, training_hour=time(18, 0))
    by_label = {d['label']: d['focus'] for d in dist}
    assert by_label['Merienda'] == 'Muchos carbohidratos'
    assert by_label['Cena'] == 'Recuperacion'
