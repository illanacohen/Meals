"""Aggregate meal ingredients into a shopping list."""

from __future__ import annotations

from collections import defaultdict

from app.services.food_catalog import FOOD_CATALOG, lookup_food, normalize_food_name

# Merge common variants into one shopping line
CANONICAL_NAMES = {
    'huevos': 'huevo',
    'rebanada de pan': 'pan',
}


def canonical_food_name(name: str) -> str:
    key = normalize_food_name(name)
    return CANONICAL_NAMES.get(key, key)


def _display_amount(name: str, total_grams: float) -> dict:
    """Pick a shopper-friendly unit (kg / g / unit / ml)."""
    food = lookup_food(name) or FOOD_CATALOG.get(name) or {}
    default_unit = food.get('default_unit', 'g')
    grams_per_unit = float(food.get('grams_per_unit') or 1.0)

    if default_unit == 'unit' and grams_per_unit > 0:
        quantity = round(total_grams / grams_per_unit)
        quantity = max(1, int(quantity)) if total_grams > 0 else 0
        label = name
        if name == 'huevo' and quantity != 1:
            label = 'huevos'
        return {
            'quantity': float(quantity),
            'unit': 'unit',
            'grams': round(total_grams, 1),
            'display': f'{quantity} {label}',
        }

    if default_unit == 'ml' and grams_per_unit > 0:
        ml = round(total_grams / grams_per_unit)
        return {
            'quantity': float(ml),
            'unit': 'ml',
            'grams': round(total_grams, 1),
            'display': f'{ml} ml {name}',
        }

    grams = round(total_grams, 0)
    if grams >= 1000:
        kg = round(grams / 1000.0, 2)
        # Drop trailing .0 for clean "1.4 kg"
        kg_str = f'{kg:g}'
        return {
            'quantity': kg,
            'unit': 'kg',
            'grams': grams,
            'display': f'{kg_str} kg {name}',
        }

    return {
        'quantity': grams,
        'unit': 'g',
        'grams': grams,
        'display': f'{int(grams)} g {name}',
    }


def build_shopping_list(items: list) -> list[dict]:
    """Sum MealItem-like objects by food name.

    Each item needs `.name` and `.grams` (and optionally `.quantity` / `.unit`).
    """
    totals: dict[str, float] = defaultdict(float)
    for item in items:
        key = canonical_food_name(item.name)
        totals[key] += float(item.grams or 0)

    lines = []
    for name in sorted(totals.keys()):
        grams = totals[name]
        if grams <= 0:
            continue
        amount = _display_amount(name, grams)
        lines.append({
            'name': name,
            **amount,
        })
    return lines


def collect_items_from_plans(plans: list) -> list:
    items = []
    for plan in plans:
        for slot in plan.slots:
            for meal in slot.meals:
                items.extend(meal.items)
    return items
