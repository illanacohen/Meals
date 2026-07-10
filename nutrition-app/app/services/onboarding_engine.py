"""Onboarding calculations: BMR, TDEE, target macros, meal distribution."""

from __future__ import annotations

ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

DEFICIT_FACTORS = {
    'mild': 0.90,       # ~10% deficit
    'moderate': 0.80,   # ~20% deficit
    'aggressive': 0.75, # ~25% deficit
}

SURPLUS_FACTORS = {
    'mild': 1.10,       # ~10% surplus (clean bulk)
    'moderate': 1.15,   # ~15% surplus
}

# Slot labels aligned with DEFAULT_SLOT_LABELS
SLOT_LABELS = {
    1: 'Desayuno',
    2: 'Almuerzo',
    3: 'Merienda',
    4: 'Cena',
}


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """Mifflin-St Jeor."""
    if sex == 'male':
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def calculate_tdee(bmr: float, activity_level: str) -> float:
    return bmr * ACTIVITY_MULTIPLIERS[activity_level]


def calculate_target_calories(
    tdee: float,
    goal: str,
    deficit_intensity: str | None = None,
    surplus_intensity: str | None = None,
) -> float:
    if goal == 'maintenance':
        return tdee
    if goal == 'deficit':
        factor = DEFICIT_FACTORS[deficit_intensity or 'moderate']
        return tdee * factor
    if goal == 'surplus':
        factor = SURPLUS_FACTORS[surplus_intensity or 'mild']
        return tdee * factor
    raise ValueError(f'Unknown goal: {goal}')


def calculate_macro_targets(weight_kg: float, calories: float, goal: str) -> dict:
    """Protein by bodyweight; fat ~25-30% kcal; carbs fill the rest; fiber heuristic."""
    if goal == 'deficit':
        protein_per_kg = 2.2
        fat_ratio = 0.25
    elif goal == 'surplus':
        protein_per_kg = 1.8
        fat_ratio = 0.25
    else:
        protein_per_kg = 1.8
        fat_ratio = 0.28

    protein = weight_kg * protein_per_kg
    fat = (calories * fat_ratio) / 9
    carbs = max(0.0, (calories - protein * 4 - fat * 9) / 4)
    fiber = min(40.0, max(25.0, calories / 1000 * 14))

    return {
        'calories': round(calories, 1),
        'protein': round(protein, 1),
        'fat': round(fat, 1),
        'carbs': round(carbs, 1),
        'fiber': round(fiber, 1),
    }


def _base_distribution(meals_per_day: int) -> dict[int, float]:
    """Default calorie share per slot position (1-4)."""
    if meals_per_day <= 3:
        return {1: 0.30, 2: 0.40, 3: 0.0, 4: 0.30}
    return {1: 0.25, 2: 0.30, 3: 0.20, 4: 0.25}


def distribute_macros(
    targets: dict,
    *,
    training_time: str | None,
    hunger_pattern: str | None,
    prefers_larger_post_workout: bool,
    meals_per_day: int = 4,
) -> list[dict]:
    """Heuristic distribution to reduce hunger and fuel training."""
    shares = _base_distribution(meals_per_day)

    if training_time == 'morning' and prefers_larger_post_workout:
        shares[1] += 0.05
        shares[3] -= 0.05
    elif training_time == 'afternoon' and prefers_larger_post_workout:
        shares[2] += 0.05
        shares[1] -= 0.025
        shares[4] -= 0.025
    elif training_time == 'evening' and prefers_larger_post_workout:
        shares[4] += 0.05
        shares[3] -= 0.05

    if hunger_pattern == 'morning':
        shares[1] += 0.05
        shares[4] -= 0.05
    elif hunger_pattern == 'evening':
        shares[4] += 0.05
        shares[1] -= 0.05

    total = sum(max(0.0, v) for v in shares.values()) or 1.0
    shares = {k: max(0.0, v) / total for k, v in shares.items()}

    training_slot = {
        'morning': 1,
        'afternoon': 2,
        'evening': 4,
    }.get(training_time or '', None)

    distribution = []
    for position in (1, 2, 3, 4):
        share = shares[position]
        if share <= 0:
            continue

        # Bias carbs toward the training meal; protein/fat follow calorie share
        carb_weight = share * (1.15 if position == training_slot else 1.0)
        distribution.append({
            'position': position,
            'label': SLOT_LABELS[position],
            'calorie_share': round(share, 3),
            'calories': round(targets['calories'] * share, 1),
            'protein': round(targets['protein'] * share, 1),
            'fat': round(targets['fat'] * share, 1),
            'carbs': round(targets['carbs'] * share, 1),  # placeholder, renormalized below
            'fiber': round(targets['fiber'] * share, 1),
            '_carb_weight': carb_weight,
        })

    carb_weight_total = sum(item['_carb_weight'] for item in distribution) or 1.0
    for item in distribution:
        item['carbs'] = round(targets['carbs'] * (item.pop('_carb_weight') / carb_weight_total), 1)

    return distribution


def run_onboarding_calculations(profile) -> dict:
    bmr = calculate_bmr(profile.weight_kg, profile.height_cm, profile.age, profile.sex)
    tdee = calculate_tdee(bmr, profile.activity_level)
    target_calories = calculate_target_calories(
        tdee,
        profile.goal,
        deficit_intensity=profile.deficit_intensity,
        surplus_intensity=profile.surplus_intensity,
    )
    targets = calculate_macro_targets(profile.weight_kg, target_calories, profile.goal)
    distribution = distribute_macros(
        targets,
        training_time=profile.training_time,
        hunger_pattern=profile.hunger_pattern,
        prefers_larger_post_workout=profile.prefers_larger_post_workout,
        meals_per_day=profile.meals_per_day,
    )
    return {
        'bmr': round(bmr, 1),
        'tdee': round(tdee, 1),
        'targets': targets,
        'distribution': distribution,
    }
