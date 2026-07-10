from datetime import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Sex(str, Enum):
    male = 'male'
    female = 'female'


class NutritionGoal(str, Enum):
    deficit = 'deficit'
    maintenance = 'maintenance'
    surplus = 'surplus'


class DeficitIntensity(str, Enum):
    mild = 'mild'
    moderate = 'moderate'
    aggressive = 'aggressive'


class SurplusIntensity(str, Enum):
    mild = 'mild'
    moderate = 'moderate'


class ActivityLevel(str, Enum):
    sedentary = 'sedentary'
    light = 'light'
    moderate = 'moderate'
    active = 'active'
    very_active = 'very_active'


class TrainingTime(str, Enum):
    morning = 'morning'
    afternoon = 'afternoon'
    evening = 'evening'
    none = 'none'


class TrainingType(str, Enum):
    strength = 'strength'
    crossfit = 'crossfit'
    running = 'running'
    mixed = 'mixed'
    other = 'other'


class TrainingLevel(str, Enum):
    beginner = 'beginner'
    intermediate = 'intermediate'
    advanced = 'advanced'


class HungerPattern(str, Enum):
    morning = 'morning'
    evening = 'evening'
    balanced = 'balanced'


class BudgetLevel(str, Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'


class OnboardingBasicsRequest(BaseModel):
    """Paso 1 obligatorio: solo lo esencial."""

    age: int = Field(ge=14, le=100)
    sex: Sex
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float = Field(gt=0, le=300)
    goal: NutritionGoal
    # Defaults so basics stay minimal
    deficit_intensity: Optional[DeficitIntensity] = DeficitIntensity.moderate
    surplus_intensity: Optional[SurplusIntensity] = SurplusIntensity.mild
    create_goal_for_today: bool = True

    @model_validator(mode='after')
    def apply_goal_defaults(self):
        if self.goal == NutritionGoal.maintenance:
            self.deficit_intensity = None
            self.surplus_intensity = None
        elif self.goal == NutritionGoal.deficit and self.deficit_intensity is None:
            self.deficit_intensity = DeficitIntensity.moderate
        elif self.goal == NutritionGoal.surplus and self.surplus_intensity is None:
            self.surplus_intensity = SurplusIntensity.mild
        return self


class OnboardingRefineRequest(BaseModel):
    """Paso 2 opcional: refinar perfil y redistribuir por horario."""

    activity_level: Optional[ActivityLevel] = None
    deficit_intensity: Optional[DeficitIntensity] = None
    surplus_intensity: Optional[SurplusIntensity] = None
    body_fat_percent: Optional[float] = Field(default=None, ge=3, le=60)
    daily_steps: Optional[int] = Field(default=None, ge=0, le=100_000)
    training_days_per_week: Optional[int] = Field(default=None, ge=0, le=7)
    training_type: Optional[TrainingType] = None
    training_level: Optional[TrainingLevel] = None
    training_time: Optional[TrainingTime] = None
    training_hour: Optional[time] = None
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    meals_per_day: Optional[int] = Field(default=None, ge=3, le=4)
    hunger_pattern: Optional[HungerPattern] = None
    prefers_larger_post_workout: Optional[bool] = None
    food_preferences: Optional[list[str]] = None
    excluded_foods: Optional[list[str]] = None
    budget_level: Optional[BudgetLevel] = None
    cooking_time_minutes: Optional[int] = Field(default=None, ge=0, le=300)
    create_goal_for_today: bool = True


# Backwards-compatible full payload (basics + optional refine fields)
class OnboardingRequest(OnboardingBasicsRequest):
    activity_level: ActivityLevel = ActivityLevel.moderate
    body_fat_percent: Optional[float] = Field(default=None, ge=3, le=60)
    daily_steps: Optional[int] = Field(default=None, ge=0, le=100_000)
    training_days_per_week: int = Field(default=0, ge=0, le=7)
    training_type: Optional[TrainingType] = None
    training_level: Optional[TrainingLevel] = None
    training_time: Optional[TrainingTime] = TrainingTime.none
    training_hour: Optional[time] = None
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    meals_per_day: int = Field(default=4, ge=3, le=4)
    hunger_pattern: Optional[HungerPattern] = HungerPattern.balanced
    prefers_larger_post_workout: bool = True
    food_preferences: Optional[list[str]] = None
    excluded_foods: Optional[list[str]] = None
    budget_level: Optional[BudgetLevel] = None
    cooking_time_minutes: Optional[int] = Field(default=None, ge=0, le=300)


class UserProfileResponse(BaseModel):
    id: int
    age: int
    sex: Sex
    weight_kg: float
    height_cm: float
    goal: NutritionGoal
    deficit_intensity: Optional[DeficitIntensity] = None
    surplus_intensity: Optional[SurplusIntensity] = None
    activity_level: ActivityLevel
    body_fat_percent: Optional[float] = None
    daily_steps: Optional[int] = None
    training_days_per_week: int
    training_type: Optional[TrainingType] = None
    training_level: Optional[TrainingLevel] = None
    training_time: Optional[TrainingTime] = None
    training_hour: Optional[time] = None
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    meals_per_day: int
    hunger_pattern: Optional[HungerPattern] = None
    prefers_larger_post_workout: bool
    food_preferences: Optional[list[str]] = None
    excluded_foods: Optional[list[str]] = None
    budget_level: Optional[BudgetLevel] = None
    cooking_time_minutes: Optional[int] = None

    model_config = {'from_attributes': True}


class MacroTargets(BaseModel):
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class MealMacroShare(BaseModel):
    position: int
    label: str
    role: str
    focus: str
    calorie_share: float
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class OnboardingGuidance(BaseModel):
    notes: list[str] = Field(default_factory=list)
    suggested_foods: list[str] = Field(default_factory=list)
    avoid_foods: list[str] = Field(default_factory=list)
    schedule_summary: Optional[str] = None


class OnboardingResponse(BaseModel):
    profile: UserProfileResponse
    bmr: float
    tdee: float
    targets: MacroTargets
    distribution: list[MealMacroShare]
    guidance: OnboardingGuidance
    goal_id: Optional[int] = None
    message: str
