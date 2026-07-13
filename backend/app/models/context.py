"""UserContext — canonical execution context aggregate.

Producers (onboarding, settings, wearables, …) write here.
Consumers (Execution Engine, AI Coach, future domains) read only from here.
"""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Time,
    func,
)

from app.db.base import Base


class UserContext(Base):
    """Single source of truth for plan generation and daily execution."""

    __tablename__ = 'user_contexts'

    id = Column(Integer, primary_key=True, index=True)
    # Stand-in until auth User exists; 1:1 with onboarding profile today.
    user_profile_id = Column(
        Integer,
        ForeignKey('user_profiles.id', ondelete='SET NULL'),
        nullable=True,
        unique=True,
        index=True,
    )
    # Reserved for future auth identity.
    user_id = Column(Integer, nullable=True, unique=True, index=True)

    # --- Identity ---
    age = Column(Integer, nullable=True)
    sex = Column(String, nullable=True)  # male | female | other
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)

    # --- Daily schedule ---
    wake_time = Column(Time, nullable=True)
    sleep_time = Column(Time, nullable=True)
    working_hours = Column(JSON, nullable=True)  # {"start": "09:00", "end": "17:00", "pattern": "..."}
    preferred_training_time = Column(Time, nullable=True)
    preferred_meal_times = Column(JSON, nullable=True)  # list[str] or slot→time map
    timezone = Column(String, nullable=True, default='UTC')

    # --- Preferences ---
    preferences = Column(JSON, nullable=True)  # free-form bag (cooking_time_minutes, …)
    favorite_foods = Column(JSON, nullable=True)  # list[str]
    disliked_foods = Column(JSON, nullable=True)  # list[str]
    preferred_training_style = Column(String, nullable=True)
    preferred_learning_style = Column(String, nullable=True)

    # --- Constraints ---
    dietary_restrictions = Column(JSON, nullable=True)  # list[str]
    food_intolerances = Column(JSON, nullable=True)  # list[str]
    equipment = Column(JSON, nullable=True)  # list[str]
    injuries = Column(JSON, nullable=True)  # list[str] | structured
    mobility_limitations = Column(JSON, nullable=True)
    budget = Column(String, nullable=True)  # low | medium | high
    available_time = Column(Integer, nullable=True)  # discretionary minutes / day
    gym_access = Column(Boolean, nullable=True)
    work_schedule_constraints = Column(JSON, nullable=True)

    # --- Execution profile ---
    energy_profile = Column(JSON, nullable=True)  # e.g. {"morning": "high", "evening": "low"}
    motivation_style = Column(String, nullable=True)
    discipline_level = Column(String, nullable=True)
    planning_style = Column(String, nullable=True)
    notification_preferences = Column(JSON, nullable=True)

    # --- Behavior (cached / derived signals) ---
    current_streaks = Column(JSON, nullable=True)
    completed_habits = Column(JSON, nullable=True)
    adherence_score = Column(Float, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
