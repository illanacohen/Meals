from pydantic import BaseModel


class CreateMeal(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float 