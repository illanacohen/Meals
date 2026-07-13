"""API schemas for the UserContext aggregate."""

from __future__ import annotations

from datetime import datetime, time
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserContextUpdate(BaseModel):
    """Partial update — only set fields are applied."""

    age: Optional[int] = Field(default=None, ge=1, le=120)
    sex: Optional[str] = None
    height_cm: Optional[float] = Field(default=None, gt=0, le=300)
    weight_kg: Optional[float] = Field(default=None, gt=0, le=500)

    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    working_hours: Optional[dict[str, Any]] = None
    preferred_training_time: Optional[time] = None
    preferred_meal_times: Optional[Any] = None
    timezone: Optional[str] = None

    preferences: Optional[dict[str, Any]] = None
    favorite_foods: Optional[list[str]] = None
    disliked_foods: Optional[list[str]] = None
    preferred_training_style: Optional[str] = None
    preferred_learning_style: Optional[str] = None

    dietary_restrictions: Optional[list[str]] = None
    food_intolerances: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    injuries: Optional[Any] = None
    mobility_limitations: Optional[Any] = None
    budget: Optional[str] = None
    available_time: Optional[int] = Field(default=None, ge=0, le=1440)
    gym_access: Optional[bool] = None
    work_schedule_constraints: Optional[Any] = None

    energy_profile: Optional[dict[str, Any]] = None
    motivation_style: Optional[str] = None
    discipline_level: Optional[str] = None
    planning_style: Optional[str] = None
    notification_preferences: Optional[dict[str, Any]] = None

    current_streaks: Optional[Any] = None
    completed_habits: Optional[Any] = None
    adherence_score: Optional[float] = Field(default=None, ge=0, le=100)


class UserContextResponse(BaseModel):
    id: int
    user_profile_id: Optional[int] = None
    user_id: Optional[int] = None

    age: Optional[int] = None
    sex: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None

    wake_time: Optional[time] = None
    sleep_time: Optional[time] = None
    working_hours: Optional[dict[str, Any]] = None
    preferred_training_time: Optional[time] = None
    preferred_meal_times: Optional[Any] = None
    timezone: Optional[str] = None

    preferences: Optional[dict[str, Any]] = None
    favorite_foods: Optional[list[str]] = None
    disliked_foods: Optional[list[str]] = None
    preferred_training_style: Optional[str] = None
    preferred_learning_style: Optional[str] = None

    dietary_restrictions: Optional[list[str]] = None
    food_intolerances: Optional[list[str]] = None
    equipment: Optional[list[str]] = None
    injuries: Optional[Any] = None
    mobility_limitations: Optional[Any] = None
    budget: Optional[str] = None
    available_time: Optional[int] = None
    gym_access: Optional[bool] = None
    work_schedule_constraints: Optional[Any] = None

    energy_profile: Optional[dict[str, Any]] = None
    motivation_style: Optional[str] = None
    discipline_level: Optional[str] = None
    planning_style: Optional[str] = None
    notification_preferences: Optional[dict[str, Any]] = None

    current_streaks: Optional[Any] = None
    completed_habits: Optional[Any] = None
    adherence_score: Optional[float] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {'from_attributes': True}
