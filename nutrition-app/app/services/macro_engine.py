def calculate_daily_totals(meals):
    return {
        'calories': sum(meal.calories for meal in meals),
        'protein': sum(meal.protein for meal in meals),
        'fat': sum(meal.fat for meal in meals),
        'carbs': sum(meal.carbs for meal in meals),
        'fiber': sum(meal.fiber for meal in meals),
    }


def calculate_remaining(goal, totals):
    return {
        'calories': goal.calories - totals['calories'],
        'protein': goal.protein - totals['protein'],
        'fat': goal.fat - totals['fat'],
        'carbs': goal.carbs - totals['carbs'],
        'fiber': goal.fiber - totals['fiber'],
    }
