"""Generate a meal that fits remaining macros using the user's foods."""

from __future__ import annotations

from app.services.food_catalog import (
    CARB_FOODS,
    FAT_FOODS,
    FOOD_CATALOG,
    PROTEIN_FOODS,
    VEG_FOODS,
    lookup_food,
    macros_for_grams,
    normalize_food_name,
    quantity_from_grams,
)

SLOT_NAMES = {
    1: 'Desayuno',
    2: 'Almuerzo',
    3: 'Merienda',
    4: 'Cena',
}


def _sum_macros(parts: list[dict]) -> dict:
    totals = {'calories': 0.0, 'protein': 0.0, 'fat': 0.0, 'carbs': 0.0, 'fiber': 0.0}
    for part in parts:
        for key in totals:
            totals[key] += part.get(key, 0.0)
    return {k: round(v, 1) for k, v in totals.items()}


def _fit_score(remaining: dict, actual: dict) -> float:
    """Lower is better. Penalize going over; reward filling remaining."""
    score = 0.0
    for key in ('protein', 'fat', 'carbs', 'calories'):
        rem = max(0.0, remaining.get(key, 0.0))
        got = actual.get(key, 0.0)
        if rem <= 0:
            score += got * 2  # leftover budget already empty
            continue
        if got > rem * 1.05:
            score += (got - rem) * 5
        else:
            score += abs(rem - got) / rem
    return score


def _scale_template(template, remaining: dict) -> dict | None:
    if template.calories <= 0:
        return None

    ratios = []
    for key in ('protein', 'fat', 'carbs', 'calories'):
        target = getattr(template, key, 0) or 0
        rem = remaining.get(key, 0) or 0
        if target > 0 and rem > 0:
            ratios.append(rem / target)
    if not ratios:
        return None

    scale = min(ratios)
    scale = max(0.35, min(scale, 1.25))
    if scale < 0.35:
        return None

    items = []
    for item in template.items:
        grams = round(item.grams * scale, 0)
        if grams <= 0:
            continue
        qty, unit = quantity_from_grams(item.name, grams)
        if unit == 'g':
            qty = grams
        macros = macros_for_grams(item.name, grams) if lookup_food(item.name) else {
            'calories': round(template.calories * (grams / max(template.items[0].grams * scale, 1)), 1)
            if template.items else 0,
            'protein': 0, 'fat': 0, 'carbs': 0, 'fiber': 0,
        }
        # Prefer proportional macros from template when food has no catalog macros
        if not lookup_food(item.name):
            share = grams / max(sum(i.grams for i in template.items) * scale, 1)
            macros = {
                'calories': round(template.calories * scale * share, 1),
                'protein': round(template.protein * scale * share, 1),
                'fat': round(template.fat * scale * share, 1),
                'carbs': round(template.carbs * scale * share, 1),
                'fiber': round(template.fiber * scale * share, 1),
            }
        items.append({
            'name': item.name,
            'quantity': qty,
            'unit': unit,
            'grams': grams,
            **macros,
        })

    actual = {
        'calories': round(template.calories * scale, 1),
        'protein': round(template.protein * scale, 1),
        'fat': round(template.fat * scale, 1),
        'carbs': round(template.carbs * scale, 1),
        'fiber': round(template.fiber * scale, 1),
    }
    # Prefer catalog-summed macros when available
    if items and all(lookup_food(i['name']) for i in items):
        actual = _sum_macros(items)

    return {
        'source': 'library',
        'template_id': template.id,
        'template_name': template.name,
        'scale': round(scale, 2),
        'name': template.name,
        'items': items,
        'macros': actual,
        'score': _fit_score(remaining, actual),
    }


def _pick_food(candidates: tuple[str, ...], preferred: list[str], excluded: set[str]) -> str | None:
    preferred_norm = [normalize_food_name(p) for p in preferred]
    for name in preferred_norm:
        if name in excluded:
            continue
        if name in FOOD_CATALOG and name in candidates:
            return name
    for name in candidates:
        if name not in excluded and name in FOOD_CATALOG:
            return name
    return None


def _grams_for_macro(food: str, macro: str, target: float) -> float:
    per = FOOD_CATALOG[food]['per_100g'][macro]
    if per <= 0 or target <= 0:
        return 0.0
    grams = (target / per) * 100.0
    return max(20.0, min(400.0, round(grams, 0)))


def _build_from_foods(remaining: dict, preferred: list[str], excluded: list[str]) -> dict:
    excluded_set = {normalize_food_name(x) for x in excluded}
    protein_food = _pick_food(PROTEIN_FOODS, preferred, excluded_set)
    carb_food = _pick_food(CARB_FOODS, preferred, excluded_set)
    fat_food = _pick_food(FAT_FOODS, preferred, excluded_set)
    veg_food = _pick_food(VEG_FOODS, preferred, excluded_set)

    parts = []

    if protein_food and remaining.get('protein', 0) > 0:
        grams = _grams_for_macro(protein_food, 'protein', remaining['protein'] * 0.85)
        qty, unit = quantity_from_grams(protein_food, grams)
        if unit == 'g':
            qty = grams
        macros = macros_for_grams(protein_food, grams)
        parts.append({'name': protein_food, 'quantity': qty, 'unit': unit, 'grams': grams, **macros})

    used = _sum_macros(parts)
    carbs_left = max(0.0, remaining.get('carbs', 0) - used['carbs'])
    if carb_food and carbs_left > 5:
        grams = _grams_for_macro(carb_food, 'carbs', carbs_left * 0.9)
        # avoid duplicating same food
        if carb_food == protein_food:
            carb_food = _pick_food(
                tuple(c for c in CARB_FOODS if c != protein_food),
                preferred,
                excluded_set,
            )
        if carb_food:
            qty, unit = quantity_from_grams(carb_food, grams)
            if unit == 'g':
                qty = grams
            macros = macros_for_grams(carb_food, grams)
            parts.append({'name': carb_food, 'quantity': qty, 'unit': unit, 'grams': grams, **macros})

    used = _sum_macros(parts)
    fat_left = max(0.0, remaining.get('fat', 0) - used['fat'])
    if fat_food and fat_left > 3 and fat_food not in {p['name'] for p in parts}:
        grams = _grams_for_macro(fat_food, 'fat', fat_left * 0.8)
        grams = min(grams, 40.0)  # nuts are dense
        qty, unit = quantity_from_grams(fat_food, grams)
        if unit == 'g':
            qty = grams
        macros = macros_for_grams(fat_food, grams)
        parts.append({'name': fat_food, 'quantity': qty, 'unit': unit, 'grams': grams, **macros})

    if veg_food and veg_food not in {p['name'] for p in parts}:
        grams = 150.0
        qty, unit = quantity_from_grams(veg_food, grams)
        if unit == 'g':
            qty = grams
        macros = macros_for_grams(veg_food, grams)
        # only add veg if it doesn't blow carb budget badly
        if used['carbs'] + macros['carbs'] <= remaining.get('carbs', 0) * 1.15 + 10:
            parts.append({'name': veg_food, 'quantity': qty, 'unit': unit, 'grams': grams, **macros})

    actual = _sum_macros(parts)
    name_bits = [p['name'].capitalize() for p in parts[:3]]
    meal_name = ' + '.join(name_bits) if name_bits else 'Comida sugerida'

    return {
        'source': 'generated',
        'template_id': None,
        'template_name': None,
        'scale': 1.0,
        'name': meal_name,
        'items': [
            {
                'name': p['name'],
                'quantity': p['quantity'],
                'unit': p['unit'],
                'grams': p['grams'],
            }
            for p in parts
        ],
        'macros': actual,
        'score': _fit_score(remaining, actual),
    }


def generate_meal_for_remaining(
    remaining: dict,
    *,
    meal_name: str | None = None,
    preferred_foods: list[str] | None = None,
    excluded_foods: list[str] | None = None,
    templates: list | None = None,
    slot_position: int | None = None,
) -> dict:
    preferred = preferred_foods or []
    excluded = excluded_foods or []

    candidates = []
    for template in templates or []:
        scaled = _scale_template(template, remaining)
        if scaled:
            candidates.append(scaled)

    generated = _build_from_foods(remaining, preferred, excluded)
    candidates.append(generated)

    best = min(candidates, key=lambda c: c['score'])
    label = SLOT_NAMES.get(slot_position or 0)
    if meal_name:
        best['name'] = meal_name
    elif label and best['source'] == 'generated':
        best['name'] = f'{label}: {best["name"]}'

    best['remaining_before'] = {
        'calories': round(remaining.get('calories', 0), 1),
        'protein': round(remaining.get('protein', 0), 1),
        'fat': round(remaining.get('fat', 0), 1),
        'carbs': round(remaining.get('carbs', 0), 1),
        'fiber': round(remaining.get('fiber', 0), 1),
    }
    macros = best['macros']
    best['remaining_after'] = {
        'calories': round(remaining.get('calories', 0) - macros['calories'], 1),
        'protein': round(remaining.get('protein', 0) - macros['protein'], 1),
        'fat': round(remaining.get('fat', 0) - macros['fat'], 1),
        'carbs': round(remaining.get('carbs', 0) - macros['carbs'], 1),
        'fiber': round(remaining.get('fiber', 0) - macros.get('fiber', 0), 1),
    }
    best['message'] = (
        f'Suggested "{best["name"]}" from {best["source"]} '
        f'to fit remaining macros.'
    )
    return best
