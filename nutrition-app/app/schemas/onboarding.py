from datetime import time
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class Sex(str, Enum):
    male = 'male'
    female = 'female'


class NutritionGoal(str, Enum):
    deficit = 'deficit'          # definición
    maintenance = 'maintenance'
    surplus = 'surplus'          # volumen limpio


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


class HungerPattern(str, Enum):
    morning = 'morning'
    evening = 'evening'
    balanced = 'balanced'


class OnboardingRequest(BaseModel):
    # Basics
    age: int = Field(ge=14, le=100)
    sex: Sex
    weight_kg: float = Field(gt=0, le=400)
    height_cm: float = Field(gt=0, le=300)
    goal: NutritionGoal

    # Intensities (required depending on goal)
    deficit_intensity: Optional[DeficitIntensity] = None
    surplus_intensity: Optional[SurplusIntensity] = None

    # Intelligent extras
    activity_level: ActivityLevel
    training_days_per_week: int = Field(default=0, ge=0, le=7)
    training_time: Optional[TrainingTime] = TrainingTime.none
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    meals_per_day: int = Field(default=4, ge=3, le=4)
    hunger_pattern: Optional[HungerPattern] = HungerPattern.balanced
    prefers_larger_post_workout: bool = True

    # Side effect: create/update today's DailyGoal from computed targets
    create_goal_for_today: bool = True

    @model_validator(mode='after')
    def validate_goal_intensities(self):
        if self.goal == NutritionGoal.deficit and self.deficit_intensity is None:
            raise ValueError('deficit_intensity is required when goal is deficit')
        if self.goal == NutritionGoal.surplus and self.surplus_intensity is None:
            raise ValueError('surplus_intensity is required when goal is surplus')
        if self.goal == NutritionGoal.maintenance:
            self.deficit_intensity = None
            self.surplus_intensity = None
        return self


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
    training_days_per_week: int
    training_time: Optional[TrainingTime] = None
    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    meals_per_day: int
    hunger_pattern: Optional[HungerPattern] = None
    prefers_larger_post_workout: bool

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
    calorie_share: float
    calories: float
    protein: float
    fat: float
    carbs: float
    fiber: float


class OnboardingResponse(BaseModel):
    profile: UserProfileResponse
    bmr: float
    tdee: float
    targets: MacroTargets
    distribution: list[MealMacroShare]
    goal_id: Optional[int] = None
    message: str
