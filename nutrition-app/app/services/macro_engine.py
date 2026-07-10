

def calculate_daily_totals(meals):
    return {
        'calories': sum(grams.calories for grams in meals),
        'protein': sum(grams.protein for grams in meals),
        'fat': sum(grams.fat for grams in meals),
        'carbs': sum(grams.carbs for grams in meals),
        'fiber': sum(grams.fiber for grams in meals),
    }