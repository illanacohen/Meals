MACRO_FIELDS = ('calories', 'protein', 'fat', 'carbs', 'fiber')


def calculate_daily_totals(meals):
    return {
        field: sum(getattr(meal, field) for meal in meals)
        for field in MACRO_FIELDS
    }


def calculate_remaining(goal, totals):
    return {
        field: getattr(goal, field) - totals[field]
        for field in MACRO_FIELDS
    }


def validate_plan_against_goal(goal, totals, tolerance_percent: float = 5.0):
    """Compare plan totals to a daily goal within a relative tolerance.

    A macro is OK when |actual - goal| <= goal * (tolerance_percent / 100).
    If the goal value is 0, only an exact match (actual == 0) is OK.
    """
    macros = []
    all_ok = True

    for field in MACRO_FIELDS:
        target = getattr(goal, field)
        actual = totals[field]
        difference = actual - target

        if target == 0:
            within_tolerance = actual == 0
            allowed_delta = 0.0
        else:
            allowed_delta = abs(target) * (tolerance_percent / 100.0)
            within_tolerance = abs(difference) <= allowed_delta

        if within_tolerance:
            status = 'ok'
        elif difference < 0:
            status = 'under'
            all_ok = False
        else:
            status = 'over'
            all_ok = False

        macros.append({
            'nutrient': field,
            'goal': target,
            'actual': actual,
            'difference': difference,
            'allowed_delta': allowed_delta,
            'status': status,
        })

    if all_ok:
        message = 'Plan matches daily goal within tolerance'
    else:
        failing = [m['nutrient'] for m in macros if m['status'] != 'ok']
        message = f'Plan does not match goal for: {", ".join(failing)}'

    return {
        'is_valid': all_ok,
        'tolerance_percent': tolerance_percent,
        'macros': macros,
        'message': message,
    }
