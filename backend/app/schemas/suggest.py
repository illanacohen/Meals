from typing import Optional

from pydantic import BaseModel, Field, model_validator

from app.schemas.meal import MealResponse, MealUnit


class RemainingMacros(BaseModel):
    """Leftover macros the meal should fill (request input)."""

    calories: Optional[float] = None
    protein: float = Field(ge=0)
    fat: float = Field(ge=0)
    carbs: float = Field(ge=0)
    fiber: Optional[float] = Field(default=0, ge=0)

    @model_validator(mode='after')
    def fill_calories(self):
        if self.calories is None:
            self.calories = self.protein * 4 + self.carbs * 4 + self.fat * 9
        return self


class MacroSnapshot(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float = 0


class SuggestMealRequest(BaseModel):
    """Generate a meal for leftover macros.

    Provide either explicit `remaining` OR `plan_id` (uses goal - plan totals).
    """

    prompt: Optional[str] = Field(
        default=None,
        description='Natural request, e.g. "Generame una cena."',
    )
    remaining: Optional[RemainingMacros] = None
    plan_id: Optional[int] = None
    slot_position: int = Field(default=4, ge=1, le=4)
    meal_name: Optional[str] = None
    preferred_foods: Optional[list[str]] = None
    excluded_foods: Optional[list[str]] = None
    use_library: bool = True
    save_to_slot: bool = False

    @model_validator(mode='after')
    def require_source(self):
        if self.remaining is None and self.plan_id is None:
            raise ValueError('Provide remaining macros or plan_id')
        return self


class SuggestedItem(BaseModel):
    name: str
    quantity: float
    unit: MealUnit
    grams: float


class SuggestMealResponse(BaseModel):
    name: str
    source: str
    template_id: Optional[int] = None
    template_name: Optional[str] = None
    scale: float
    items: list[SuggestedItem]
    macros: MacroSnapshot
    remaining_before: MacroSnapshot
    remaining_after: MacroSnapshot
    message: str
    saved_meal: Optional[MealResponse] = None
    prompt: Optional[str] = None
