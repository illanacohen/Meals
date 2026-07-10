from sqlalchemy import Column, Integer, String, Float, Time, Boolean, JSON

from app.database.base import Base


class UserProfile(Base):
    """Single-user onboarding profile (no auth yet)."""

    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, index=True)

    # Required basics
    age = Column(Integer, nullable=False)
    gender = Column(String, nullable=False)  # male | female
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)
    goal = Column(String, nullable=False)  # deficit | maintenance | surplus
    deficit_intensity = Column(String, nullable=True)
    surplus_intensity = Column(String, nullable=True)
    activity_level = Column(String, nullable=False)

    # Optional body / activity detail
    body_fat_percent = Column(Float, nullable=True)
    daily_steps = Column(Integer, nullable=True)

    # Training
    training_days_per_week = Column(Integer, nullable=False, default=0)
    training_type = Column(String, nullable=True)  # strength | crossfit | running | mixed | other
    training_level = Column(String, nullable=True)  # beginner | intermediate | advanced
    training_time = Column(String, nullable=True)  # morning | afternoon | evening | none
    training_hour = Column(Time, nullable=True)

    # Lifestyle
    wake_time = Column(Time, nullable=True)
    sleep_time = Column(Time, nullable=True)
    meals_per_day = Column(Integer, nullable=False, default=4)
    hunger_pattern = Column(String, nullable=True)
    prefers_larger_post_workout = Column(Boolean, nullable=False, default=True)

    # Food / practical constraints
    food_preferences = Column(JSON, nullable=True)  # list[str]
    excluded_foods = Column(JSON, nullable=True)  # list[str]
    budget_level = Column(String, nullable=True)  # low | medium | high
    cooking_time_minutes = Column(Integer, nullable=True)
