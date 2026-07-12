"""Daily Planner domain: schedule policy, blocks, task templates, plan tasks."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class DaySchedulePolicy(Base):
    """Wake/sleep-relative day structure and placement rules."""

    __tablename__ = 'day_schedule_policies'

    id = Column(Integer, primary_key=True, index=True)
    user_profile_id = Column(
        Integer,
        ForeignKey('user_profiles.id', ondelete='CASCADE'),
        nullable=True,
        unique=True,
    )
    wake_time = Column(Time, nullable=False)
    sleep_time = Column(Time, nullable=False)
    work_pattern = Column(String, nullable=False, default='variable')
    work_start = Column(Time, nullable=True)
    work_end = Column(Time, nullable=True)
    training_days = Column(JSON, nullable=True)
    training_hour = Column(Time, nullable=True)
    meals_per_day = Column(Integer, nullable=False, default=4)
    block1_ratio = Column(Float, nullable=False, default=0.25)
    block2_ratio = Column(Float, nullable=False, default=0.45)
    block3_ratio = Column(Float, nullable=False, default=0.30)
    delay_first_meal = Column(Boolean, nullable=False, default=False)
    timezone = Column(String, nullable=True, default='UTC')


class DayBlock(Base):
    """Concrete time window for a plan on a calendar date."""

    __tablename__ = 'day_blocks'
    __table_args__ = (
        UniqueConstraint('plan_id', 'date', 'block_type', name='uq_day_blocks_plan_date_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    block_type = Column(String, nullable=False)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)

    plan = relationship('Plan', back_populates='day_blocks')


class TaskTemplate(Base):
    """Reusable action catalog (system hygiene pack + custom)."""

    __tablename__ = 'task_templates'

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False, default='custom')
    default_friction = Column(Integer, nullable=False, default=3)
    default_priority = Column(Integer, nullable=False, default=3)
    default_duration_minutes = Column(Integer, nullable=False, default=5)
    default_block_preference = Column(String, nullable=False, default='any')
    is_system = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)

    plan_tasks = relationship('PlanTask', back_populates='template')


class PlanTask(Base):
    """Task subscribed to a Plan (feeds DailyTask projection)."""

    __tablename__ = 'plan_tasks'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    template_id = Column(Integer, ForeignKey('task_templates.id', ondelete='SET NULL'), nullable=True)
    habit_id = Column(Integer, ForeignKey('habits.id', ondelete='SET NULL'), nullable=True)
    title = Column(String, nullable=False)
    friction = Column(Integer, nullable=False, default=3)
    priority = Column(Integer, nullable=False, default=3)
    duration_minutes = Column(Integer, nullable=False, default=5)
    frequency = Column(String, nullable=False, default='daily')
    preferred_block = Column(String, nullable=False, default='any')
    forbidden_blocks = Column(JSON, nullable=True)
    depends_on_plan_task_id = Column(
        Integer,
        ForeignKey('plan_tasks.id', ondelete='SET NULL'),
        nullable=True,
    )
    active = Column(Boolean, nullable=False, default=True)

    plan = relationship('Plan', back_populates='plan_tasks')
    template = relationship('TaskTemplate', back_populates='plan_tasks')
