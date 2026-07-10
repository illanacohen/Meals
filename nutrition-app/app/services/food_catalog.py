"""Local food catalog that simulates food lookup (no AI).

Maps common food names to a default unit and grams-per-unit so items
like eggs can be logged as units and converted to grams.
"""

from __future__ import annotations

FOOD_CATALOG: dict[str, dict] = {
    # Pieces / units
    'huevo': {'default_unit': 'unit', 'grams_per_unit': 50.0},
    'huevos': {'default_unit': 'unit', 'grams_per_unit': 50.0},
    'banana': {'default_unit': 'unit', 'grams_per_unit': 120.0},
    'manzana': {'default_unit': 'unit', 'grams_per_unit': 180.0},
    'rebanada de pan': {'default_unit': 'unit', 'grams_per_unit': 30.0},
    'pan': {'default_unit': 'unit', 'grams_per_unit': 30.0},
    # Liquids (ml ≈ g for water-like density in this simple catalog)
    'leche': {'default_unit': 'ml', 'grams_per_unit': 1.03},
    'yogur': {'default_unit': 'g', 'grams_per_unit': 1.0},
    # Weight-based foods (1 unit of measure = 1 g)
    'pollo': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'arroz': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'avena': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'zanahoria': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'cebolla': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'zapallito': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'pescado': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'papa': {'default_unit': 'g', 'grams_per_unit': 1.0},
    'nueces': {'default_unit': 'g', 'grams_per_unit': 1.0},
}

ALLOWED_UNITS = frozenset({'g', 'unit', 'ml'})


class FoodResolutionError(ValueError):
    """Raised when grams cannot be resolved for an item."""


def normalize_food_name(name: str) -> str:
    return name.strip().lower()


def lookup_food(name: str) -> dict | None:
    return FOOD_CATALOG.get(normalize_food_name(name))


def resolve_item_grams(
    name: str,
    quantity: float,
    unit: str,
    grams_per_unit: float | None = None,
) -> float:
    """Resolve an item to grams using catalog and/or explicit grams_per_unit."""
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
    """Build MealItem column values from a MealItemCreate-like object."""
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
