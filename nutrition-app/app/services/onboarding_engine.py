"""Onboarding calculations: BMR, TDEE, target macros, schedule-based distribution."""

from __future__ import annotations

ACTIVITY_MULTIPLIERS = {
    'sedentary': 1.2,
    'light': 1.375,
    'moderate': 1.55,
    'active': 1.725,
    'very_active': 1.9,
}

DEFICIT_FACTORS = {
    'mild': 0.90,
    'moderate': 0.80,
    'aggressive': 0.75,
}

SURPLUS_FACTORS = {
    'mild': 1.10,
    'moderate': 1.15,
}

SLOT_LABELS = {
    1: 'Desayuno',
    2: 'Almuerzo',
    3: 'Merienda',
    4: 'Cena',
}

KCAL_PER_STEP = 0.04

BUDGET_FOOD_SUGGESTIONS = {
    'low': ['huevo', 'avena', 'arroz', 'pollo', 'lentejas', 'banana'],
    'medium': ['yogur', 'pescado', 'papa', 'nueces', 'zapallito'],
    'high': ['salmon', 'carne magra', 'frutos secos premium', 'berries'],
}


def calculate_bmr(
    weight_kg: float,
    height_cm: float,
    age: int,
    sex: str,
    body_fat_percent: float | None = None,
) -> float:
    if body_fat_percent is not None:
        lean_mass = weight_kg * (1 - body_fat_percent / 100.0)
        return 370 + (21.6 * lean_mass)

    if sex == 'male':
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def calculate_tdee(
    bmr: float,
    activity_level: str | None,
    daily_steps: int | None = None,
    training_days_per_week: int = 0,
    training_type: str | None = None,
) -> float:
    level = activity_level or 'moderate'
    tdee = bmr * ACTIVITY_MULTIPLIERS[level]

    if daily_steps is not None:
        step_kcal = min(600.0, daily_steps * KCAL_PER_STEP)
        tdee = max(tdee, bmr * 1.2 + step_kcal)

    if training_days_per_week > 0:
        type_bonus = {
            'strength': 40,
            'crossfit': 70,
            'running': 60,
            'mixed': 55,
            'other': 45,
        }.get(training_type or 'other', 45)
        tdee += training_days_per_week * type_bonus

    return tdee


def calculate_target_calories(
    tdee: float,
    goal: str,
    deficit_intensity: str | None = None,
    surplus_intensity: str | None = None,
) -> float:
    if goal == 'maintenance':
        return tdee
    if goal == 'deficit':
        return tdee * DEFICIT_FACTORS[deficit_intensity or 'moderate']
    if goal == 'surplus':
        return tdee * SURPLUS_FACTORS[surplus_intensity or 'mild']
    raise ValueError(f'Unknown goal: {goal}')


def calculate_macro_targets(
    weight_kg: float,
    calories: float,
    goal: str,
    *,
    body_fat_percent: float | None = None,
    training_type: str | None = None,
    training_level: str | None = None,
) -> dict:
    if body_fat_percent is not None:
        mass_for_protein = weight_kg * (1 - body_fat_percent / 100.0)
    else:
        mass_for_protein = weight_kg

    if goal == 'deficit':
        protein_per_kg = 2.4
        fat_ratio = 0.25
    elif goal == 'surplus':
        protein_per_kg = 2.0
        fat_ratio = 0.25
    else:
        protein_per_kg = 1.8
        fat_ratio = 0.28

    if training_type == 'strength':
        protein_per_kg += 0.2
    elif training_type in ('crossfit', 'running', 'mixed'):
        protein_per_kg += 0.1

    if training_level == 'advanced':
        protein_per_kg += 0.1
    elif training_level == 'beginner':
        protein_per_kg -= 0.1

    protein_per_kg = max(1.4, min(2.8, protein_per_kg))

    protein = mass_for_protein * protein_per_kg
    fat = (calories * fat_ratio) / 9
    carbs = max(0.0, (calories - protein * 4 - fat * 9) / 4)

    if training_type in ('running', 'crossfit', 'mixed') and carbs < weight_kg * 3:
        fat_ratio = 0.22
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


def _resolve_training_window(training_time: str | None, training_hour) -> str:
    if training_hour is not None:
        hour = training_hour.hour
        if hour < 11:
            return 'morning'
        if hour < 16:
            return 'afternoon'
        return 'evening'
    if training_time in ('morning', 'afternoon', 'evening'):
        return training_time
    return 'none'


def _role_plan_for_window(window: str) -> dict[int, dict]:
    """Map each meal to a role based on training schedule.

    afternoon (train after lunch):
      Desayuno -> protein + fat
      Almuerzo -> high carbs
      Merienda -> recovery
      Cena -> complete macros

    morning (e.g. 7 AM):
      Desayuno -> recovery
      Almuerzo -> high carbs
      Merienda -> protein + fat
      Cena -> complete

    evening (e.g. 6 PM):
      Desayuno -> protein + fat
      Almuerzo -> balanced
      Merienda -> high carbs (pre)
      Cena -> recovery
    """
    roles = {
        'protein_fat': {
            'role': 'protein_fat',
            'focus': 'Proteina + grasa',
            'cal': 0.20, 'p': 0.28, 'f': 0.40, 'c': 0.10, 'fi': 0.20,
        },
        'high_carb': {
            'role': 'high_carb',
            'focus': 'Muchos carbohidratos',
            'cal': 0.35, 'p': 0.22, 'f': 0.12, 'c': 0.42, 'fi': 0.25,
        },
        'recovery': {
            'role': 'recovery',
            'focus': 'Recuperacion',
            'cal': 0.22, 'p': 0.30, 'f': 0.15, 'c': 0.28, 'fi': 0.25,
        },
        'complete': {
            'role': 'complete',
            'focus': 'Completar macros',
            'cal': 0.23, 'p': 0.20, 'f': 0.33, 'c': 0.20, 'fi': 0.30,
        },
        'balanced': {
            'role': 'balanced',
            'focus': 'Equilibrado',
            'cal': 0.28, 'p': 0.25, 'f': 0.25, 'c': 0.28, 'fi': 0.25,
        },
    }

    if window == 'morning':
        return {1: roles['recovery'], 2: roles['high_carb'], 3: roles['protein_fat'], 4: roles['complete']}
    if window == 'afternoon':
        return {1: roles['protein_fat'], 2: roles['high_carb'], 3: roles['recovery'], 4: roles['complete']}
    if window == 'evening':
        return {1: roles['protein_fat'], 2: roles['balanced'], 3: roles['high_carb'], 4: roles['recovery']}

    even = {
        'role': 'balanced',
        'focus': 'Distribucion pareja',
        'cal': 0.25, 'p': 0.25, 'f': 0.25, 'c': 0.25, 'fi': 0.25,
    }
    return {1: even, 2: even, 3: even, 4: even}


def distribute_macros(
    targets: dict,
    *,
    training_time: str | None,
    training_hour=None,
    hunger_pattern: str | None = None,
    prefers_larger_post_workout: bool = True,
    training_type: str | None = None,
    meals_per_day: int = 4,
) -> list[dict]:
    window = _resolve_training_window(training_time, training_hour)
    plan = _role_plan_for_window(window)

    if meals_per_day <= 3:
        plan[3] = None

    cal_weights = {pos: (spec['cal'] if spec else 0.0) for pos, spec in plan.items()}
    if hunger_pattern == 'morning' and plan.get(1):
        cal_weights[1] += 0.04
        cal_weights[4] = max(0.05, cal_weights.get(4, 0) - 0.04)
    elif hunger_pattern == 'evening' and plan.get(4):
        cal_weights[4] += 0.04
        cal_weights[1] = max(0.05, cal_weights.get(1, 0) - 0.04)

    if prefers_larger_post_workout and window != 'none':
        for pos, spec in plan.items():
            if spec and spec['role'] in ('high_carb', 'recovery'):
                cal_weights[pos] += 0.02

    cal_total = sum(cal_weights.values()) or 1.0
    cal_weights = {pos: value / cal_total for pos, value in cal_weights.items()}

    def _norm(key: str) -> dict[int, float]:
        raw = {pos: (spec[key] if spec else 0.0) for pos, spec in plan.items()}
        total = sum(raw.values()) or 1.0
        return {pos: value / total for pos, value in raw.items()}

    p_w, f_w, c_w, fi_w = _norm('p'), _norm('f'), _norm('c'), _norm('fi')

    if training_type in ('running', 'crossfit', 'mixed'):
        for pos, spec in plan.items():
            if spec and spec['role'] == 'high_carb':
                c_w[pos] *= 1.1
        c_total = sum(c_w.values()) or 1.0
        c_w = {pos: value / c_total for pos, value in c_w.items()}

    distribution = []
    for position in (1, 2, 3, 4):
        spec = plan.get(position)
        if not spec:
            continue
        distribution.append({
            'position': position,
            'label': SLOT_LABELS[position],
            'role': spec['role'],
            'focus': spec['focus'],
            'calorie_share': round(cal_weights[position], 3),
            'calories': round(targets['calories'] * cal_weights[position], 1),
            'protein': round(targets['protein'] * p_w[position], 1),
            'fat': round(targets['fat'] * f_w[position], 1),
            'carbs': round(targets['carbs'] * c_w[position], 1),
            'fiber': round(targets['fiber'] * fi_w[position], 1),
        })
    return distribution


def build_guidance(profile) -> dict:
    notes: list[str] = []
    suggested = list(BUDGET_FOOD_SUGGESTIONS.get(profile.budget_level or 'medium', []))
    avoid = list(profile.excluded_foods or [])
    window = _resolve_training_window(profile.training_time, profile.training_hour)

    schedule_summary = {
        'morning': (
            'Entreno de manana (ej. 7 AM): desayuno recuperacion, almuerzo muchos carbs, '
            'merienda proteina+grasa, cena completa macros.'
        ),
        'afternoon': (
            'Entreno despues del almuerzo: desayuno proteina+grasa, almuerzo muchos carbs, '
            'merienda recuperacion, cena completa macros.'
        ),
        'evening': (
            'Entreno de tarde/noche (ej. 6 PM): desayuno proteina+grasa, almuerzo equilibrado, '
            'merienda muchos carbs, cena recuperacion.'
        ),
        'none': (
            'Sin horario de entreno: distribucion pareja. '
            'Agrega training_hour o training_time en /onboarding/refine para reorganizar.'
        ),
    }[window]
    notes.append(schedule_summary)

    if profile.cooking_time_minutes is not None:
        if profile.cooking_time_minutes <= 15:
            notes.append('Prioritize meals under 15 minutes: eggs, yogurt, rice packs, grilled chicken.')
            suggested = ['huevo', 'yogur', 'atun', 'avena', 'banana'] + suggested
        elif profile.cooking_time_minutes <= 30:
            notes.append('You can batch-cook simple proteins and carbs 2-3 times per week.')
        else:
            notes.append('You have enough cooking time for meal prep; batch proteins and chopped veggies.')

    if profile.budget_level == 'low':
        notes.append('Favor eggs, oats, rice, legumes and chicken cuts to hit protein cheaply.')
    elif profile.budget_level == 'high':
        notes.append('Budget allows higher-quality proteins and convenience foods if adherence helps.')

    if profile.food_preferences:
        notes.append('Prefer foods aligned with: ' + ', '.join(profile.food_preferences))
        suggested = list(dict.fromkeys(list(profile.food_preferences) + suggested))

    if avoid:
        notes.append('Never include: ' + ', '.join(avoid))

    if profile.training_type == 'strength':
        notes.append('Strength focus: keep protein high and place carbs around the lifting session.')
    elif profile.training_type == 'running':
        notes.append('Running focus: bias carbs before/after runs; keep fats moderate near sessions.')
    elif profile.training_type == 'crossfit':
        notes.append('CrossFit focus: fuel the training meal with carbs + protein; avoid heavy fats pre-WO.')

    if profile.body_fat_percent is not None:
        notes.append('BMR used lean-mass (Katch-McArdle) from estimated body fat.')

    if profile.daily_steps is not None:
        notes.append(f'Daily steps ({profile.daily_steps}) were used to refine TDEE/NEAT.')

    avoid_l = {a.lower() for a in avoid}
    suggested = [s for s in dict.fromkeys(suggested) if s.lower() not in avoid_l]

    return {
        'notes': notes,
        'suggested_foods': suggested[:12],
        'avoid_foods': avoid,
        'schedule_summary': schedule_summary,
    }


def run_onboarding_calculations(profile) -> dict:
    bmr = calculate_bmr(
        profile.weight_kg,
        profile.height_cm,
        profile.age,
        profile.sex,
        body_fat_percent=profile.body_fat_percent,
    )
    tdee = calculate_tdee(
        bmr,
        getattr(profile, 'activity_level', None) or 'moderate',
        daily_steps=profile.daily_steps,
        training_days_per_week=profile.training_days_per_week or 0,
        training_type=profile.training_type,
    )
    target_calories = calculate_target_calories(
        tdee,
        profile.goal,
        deficit_intensity=profile.deficit_intensity,
        surplus_intensity=profile.surplus_intensity,
    )
    targets = calculate_macro_targets(
        profile.weight_kg,
        target_calories,
        profile.goal,
        body_fat_percent=profile.body_fat_percent,
        training_type=profile.training_type,
        training_level=profile.training_level,
    )
    distribution = distribute_macros(
        targets,
        training_time=profile.training_time,
        training_hour=profile.training_hour,
        hunger_pattern=profile.hunger_pattern,
        prefers_larger_post_workout=bool(
            profile.prefers_larger_post_workout
            if profile.prefers_larger_post_workout is not None
            else True
        ),
        training_type=profile.training_type,
        meals_per_day=profile.meals_per_day or 4,
    )
    guidance = build_guidance(profile)
    return {
        'bmr': round(bmr, 1),
        'tdee': round(tdee, 1),
        'targets': targets,
        'distribution': distribution,
        'guidance': guidance,
    }
