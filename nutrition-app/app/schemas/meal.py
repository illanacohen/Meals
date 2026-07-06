from pydantic import BaseModel


class MealCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float


class Meal(MealCreate):
    id: int

    model_config = {
        'from_attributes': True
    }