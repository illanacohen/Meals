from sqlalchemy import Column, Integer, String, Float, Time, Boolean

from app.database.base import Base


class UserProfile(Base):
    """Single-user onboarding profile (no auth yet)."""

    __tablename__ = 'user_profiles'

    id = Column(Integer, primary_key=True, index=True)

    # Body metrics
    age = Column(Integer, nullable=False)
    sex = Column(String, nullable=False)  # male | female
    weight_kg = Column(Float, nullable=False)
    height_cm = Column(Float, nullable=False)

    # Goal
    goal = Column(String, nullable=False)  # deficit | maintenance | surplus
    deficit_intensity = Column(String, nullable=True)  # mild | moderate | aggressive
    surplus_intensity = Column(String, nullable=True)  # mild | moderate

    # Lifestyle / activity (intelligent onboarding extras)
    activity_level = Column(String, nullable=False)  # sedentary..very_active
    training_days_per_week = Column(Integer, nullable=False, default=0)
    training_time = Column(String, nullable=True)  # morning | afternoon | evening | none
    wake_time = Column(Time, nullable=True)
    sleep_time = Column(Time, nullable=True)
    meals_per_day = Column(Integer, nullable=False, default=4)
    hunger_pattern = Column(String, nullable=True)  # morning | evening | balanced
    prefers_larger_post_workout = Column(Boolean, nullable=False, default=True)
