from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class MealUnit(str, Enum):
    g = 'g'
    unit = 'unit'
    ml = 'ml'


class MealItemCreate(BaseModel):
    name: str
    quantity: Optional[float] = None
    unit: MealUnit = MealUnit.g
    grams_per_unit: Optional[float] = None
    # Legacy: if only grams is sent, treat as quantity in grams
    grams: Optional[float] = None

    @model_validator(mode='after')
    def resolve_quantity(self):
        if self.quantity is None and self.grams is not None:
            self.quantity = self.grams
            self.unit = MealUnit.g
        if self.quantity is None:
            raise ValueError('Provide quantity (and unit), or grams for legacy weight-only items')
        return self


class MealItemResponse(BaseModel):
    id: int
    name: str
    quantity: float
    unit: MealUnit
    grams: float

    model_config = {
        'from_attributes': True
    }


class MealCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float
    slot_id: Optional[int] = None
    items: list[MealItemCreate] = Field(default_factory=list)


class MealUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    fiber: Optional[float] = None
    slot_id: Optional[int] = None
    items: Optional[list[MealItemCreate]] = None


class MealResponse(BaseModel):
    id: int
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float
    slot_id: Optional[int] = None
    items: list[MealItemResponse] = Field(default_factory=list)

    model_config = {
        'from_attributes': True
    }


class ErrorResponse(BaseModel):
    detail: str


class MealDelete(BaseModel):
    id: int


class Meal(MealCreate):
    id: int

    model_config = {
        'from_attributes': True
    }


class DailyGoalCreate(BaseModel):
    date: date
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class DailyGoalUpdate(BaseModel):
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    fiber: Optional[float] = None


class DailyGoalResponse(BaseModel):
    id: int
    date: date
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float

    model_config = {
        'from_attributes': True
    }


class MealPlanCreate(BaseModel):
    date: date
    name: Optional[str] = None
    goal_plan_id: Optional[int] = None
    pillar_id: Optional[int] = None


class MealSlotResponse(BaseModel):
    id: int
    plan_id: int
    position: int
    label: str
    meals: list[MealResponse] = Field(default_factory=list)

    model_config = {
        'from_attributes': True
    }


class MealPlanResponse(BaseModel):
    id: int
    date: date
    name: Optional[str] = None
    goal_plan_id: Optional[int] = None
    pillar_id: Optional[int] = None
    slots: list[MealSlotResponse] = Field(default_factory=list)

    model_config = {
        'from_attributes': True
    }


class MacroTotals(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class MealPlanSummary(BaseModel):
    plan: MealPlanResponse
    totals: MacroTotals
    goal: Optional[DailyGoalResponse] = None
    remaining: Optional[MacroTotals] = None


class MacroValidation(BaseModel):
    nutrient: str
    goal: float
    actual: float
    difference: float
    allowed_delta: float
    status: str


class PlanGoalValidation(BaseModel):
    plan_id: int
    date: date
    is_valid: bool
    tolerance_percent: float
    goal: DailyGoalResponse
    totals: MacroTotals
    remaining: MacroTotals
    macros: list[MacroValidation]
    message: str


class MealTemplateItemResponse(BaseModel):
    id: int
    name: str
    quantity: float
    unit: MealUnit
    grams: float

    model_config = {'from_attributes': True}


class MealTemplateCreate(BaseModel):
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float
    items: list[MealItemCreate] = Field(default_factory=list)


class MealTemplateUpdate(BaseModel):
    name: Optional[str] = None
    calories: Optional[float] = None
    protein: Optional[float] = None
    fat: Optional[float] = None
    carbs: Optional[float] = None
    fiber: Optional[float] = None
    items: Optional[list[MealItemCreate]] = None


class MealTemplateResponse(BaseModel):
    id: int
    name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float
    items: list[MealTemplateItemResponse] = Field(default_factory=list)

    model_config = {'from_attributes': True}


class ApplyTemplateRequest(BaseModel):
    """Optional override name when adding a library meal to a plan slot."""
    name: Optional[str] = None
