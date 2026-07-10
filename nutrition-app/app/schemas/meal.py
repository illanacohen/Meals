from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class MealItemCreate(BaseModel):
    name: str
    grams: float


class MealItemResponse(BaseModel):
    id: int
    name: str
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
