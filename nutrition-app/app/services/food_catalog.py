"""Local food catalog: units + macros per 100g (simulates food DB / AI lookup)."""

from __future__ import annotations

FOOD_CATALOG: dict[str, dict] = {
    'huevo': {
        'default_unit': 'unit',
        'grams_per_unit': 50.0,
        'per_100g': {'calories': 143, 'protein': 13, 'fat': 10, 'carbs': 1, 'fiber': 0},
    },
    'huevos': {
        'default_unit': 'unit',
        'grams_per_unit': 50.0,
        'per_100g': {'calories': 143, 'protein': 13, 'fat': 10, 'carbs': 1, 'fiber': 0},
    },
    'banana': {
        'default_unit': 'unit',
        'grams_per_unit': 120.0,
        'per_100g': {'calories': 89, 'protein': 1.1, 'fat': 0.3, 'carbs': 23, 'fiber': 2.6},
    },
    'manzana': {
        'default_unit': 'unit',
        'grams_per_unit': 180.0,
        'per_100g': {'calories': 52, 'protein': 0.3, 'fat': 0.2, 'carbs': 14, 'fiber': 2.4},
    },
    'rebanada de pan': {
        'default_unit': 'unit',
        'grams_per_unit': 30.0,
        'per_100g': {'calories': 265, 'protein': 9, 'fat': 3.2, 'carbs': 49, 'fiber': 2.7},
    },
    'pan': {
        'default_unit': 'unit',
        'grams_per_unit': 30.0,
        'per_100g': {'calories': 265, 'protein': 9, 'fat': 3.2, 'carbs': 49, 'fiber': 2.7},
    },
    'leche': {
        'default_unit': 'ml',
        'grams_per_unit': 1.03,
        'per_100g': {'calories': 42, 'protein': 3.4, 'fat': 1, 'carbs': 5, 'fiber': 0},
    },
    'yogur': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 59, 'protein': 10, 'fat': 0.4, 'carbs': 3.6, 'fiber': 0},
    },
    'pollo': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 165, 'protein': 31, 'fat': 3.6, 'carbs': 0, 'fiber': 0},
    },
    'arroz': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 130, 'protein': 2.7, 'fat': 0.3, 'carbs': 28, 'fiber': 0.4},
    },
    'avena': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 389, 'protein': 17, 'fat': 7, 'carbs': 66, 'fiber': 11},
    },
    'zanahoria': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 41, 'protein': 0.9, 'fat': 0.2, 'carbs': 10, 'fiber': 2.8},
    },
    'cebolla': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 40, 'protein': 1.1, 'fat': 0.1, 'carbs': 9, 'fiber': 1.7},
    },
    'zapallito': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 17, 'protein': 1.2, 'fat': 0.3, 'carbs': 3.1, 'fiber': 1},
    },
    'pescado': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 120, 'protein': 22, 'fat': 3, 'carbs': 0, 'fiber': 0},
    },
    'papa': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 87, 'protein': 2, 'fat': 0.1, 'carbs': 20, 'fiber': 2.2},
    },
    'batata': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 86, 'protein': 1.6, 'fat': 0.1, 'carbs': 20, 'fiber': 3},
    },
    'nueces': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 654, 'protein': 15, 'fat': 65, 'carbs': 14, 'fiber': 6.7},
    },
    'atun': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 116, 'protein': 26, 'fat': 1, 'carbs': 0, 'fiber': 0},
    },
    'lentejas': {
        'default_unit': 'g',
        'grams_per_unit': 1.0,
        'per_100g': {'calories': 116, 'protein': 9, 'fat': 0.4, 'carbs': 20, 'fiber': 8},
    },
}

ALLOWED_UNITS = frozenset({'g', 'unit', 'ml'})

PROTEIN_FOODS = ('pollo', 'pescado', 'huevo', 'yogur', 'atun', 'lentejas')
CARB_FOODS = ('arroz', 'papa', 'batata', 'avena', 'pan', 'banana', 'lentejas')
FAT_FOODS = ('nueces', 'huevo', 'leche')
VEG_FOODS = ('zapallito', 'zanahoria', 'cebolla')


class FoodResolutionError(ValueError):
    """Raised when grams cannot be resolved for an item."""


def normalize_food_name(name: str) -> str:
    return name.strip().lower()


def lookup_food(name: str) -> dict | None:
    return FOOD_CATALOG.get(normalize_food_name(name))


def macros_for_grams(name: str, grams: float) -> dict:
    food = lookup_food(name)
    if not food or 'per_100g' not in food:
        raise FoodResolutionError(f'No macro data for "{name}"')
    factor = grams / 100.0
    per = food['per_100g']
    return {
        'calories': round(per['calories'] * factor, 1),
        'protein': round(per['protein'] * factor, 1),
        'fat': round(per['fat'] * factor, 1),
        'carbs': round(per['carbs'] * factor, 1),
        'fiber': round(per['fiber'] * factor, 1),
    }


def resolve_item_grams(
    name: str,
    quantity: float,
    unit: str,
    grams_per_unit: float | None = None,
) -> float:
    if quantity < 0:
        raise FoodResolutionError('quantity must be >= 0')

    unit = unit.lower()
    if unit not in ALLOWED_UNITS:
        raise FoodResolutionError(f'Unsupported unit "{unit}". Use: g, unit, ml')

    if unit == 'g':
        return float(quantity)

    if grams_per_unit is not None:
        if grams_per_unit <= 0:
            raise FoodResolutionError('grams_per_unit must be > 0')
        return float(quantity) * float(grams_per_unit)

    food = lookup_food(name)
    if food and food.get('grams_per_unit'):
        return float(quantity) * float(food['grams_per_unit'])

    raise FoodResolutionError(
        f'Cannot resolve grams for "{name}" with unit "{unit}". '
        'Add it to the food catalog or pass grams_per_unit.'
    )


def build_meal_item_fields(item) -> dict:
    grams = resolve_item_grams(
        name=item.name,
        quantity=item.quantity,
        unit=item.unit.value if hasattr(item.unit, 'value') else item.unit,
        grams_per_unit=getattr(item, 'grams_per_unit', None),
    )
    return {
        'name': item.name,
        'quantity': float(item.quantity),
        'unit': item.unit.value if hasattr(item.unit, 'value') else str(item.unit),
        'grams': grams,
    }


def quantity_from_grams(name: str, grams: float) -> tuple[float, str]:
    """Prefer natural unit for the food when suggesting amounts."""
    food = lookup_food(name) or {}
    unit = food.get('default_unit', 'g')
    gpu = float(food.get('grams_per_unit', 1.0) or 1.0)
    if unit in ('unit', 'ml') and gpu > 0:
        qty = round(grams / gpu, 1)
        if unit == 'unit':
            qty = max(1.0, round(qty))
        return qty, unit
    return round(grams, 0), 'g'
