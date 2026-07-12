"""Core domain: Goal-oriented Plan (entity principal del planner)."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base


class Plan(Base):
    """Plan maestro orientado a un objetivo (ej. Definición 12 semanas)."""

    __tablename__ = 'plans'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    goal_type = Column(String, nullable=False)  # deficit | surplus | maintenance | performance | custom
    description = Column(Text, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    duration_weeks = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default='draft')  # draft | active | paused | completed
    strategy_notes = Column(Text, nullable=True)
    user_profile_id = Column(Integer, ForeignKey('user_profiles.id', ondelete='SET NULL'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    habits = relationship('Habit', back_populates='plan', cascade='all, delete-orphan')
    workout_program = relationship(
        'WorkoutProgram',
        back_populates='plan',
        uselist=False,
        cascade='all, delete-orphan',
    )
    daily_tasks = relationship('DailyTask', back_populates='plan', cascade='all, delete-orphan')
    progress_entries = relationship('ProgressEntry', back_populates='plan', cascade='all, delete-orphan')
    day_blocks = relationship('DayBlock', back_populates='plan', cascade='all, delete-orphan')
    plan_tasks = relationship('PlanTask', back_populates='plan', cascade='all, delete-orphan')


class Habit(Base):
    """Hábito perteneciente a un Plan."""

    __tablename__ = 'habits'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String, nullable=True)  # sleep | water | steps | reading | nutrition | other
    frequency = Column(String, nullable=False, default='daily')  # daily | weekly
    target_value = Column(Float, nullable=True)
    target_unit = Column(String, nullable=True)
    time_of_day = Column(String, nullable=True)  # morning | afternoon | evening | anytime
    difficulty = Column(String, nullable=True)  # easy | medium | hard
    is_active = Column(Boolean, nullable=False, default=True)

    plan = relationship('Plan', back_populates='habits')
    completions = relationship('HabitCompletion', back_populates='habit', cascade='all, delete-orphan')


class HabitCompletion(Base):
    __tablename__ = 'habit_completions'
    __table_args__ = (
        UniqueConstraint('habit_id', 'date', name='uq_habit_completions_habit_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    habit_id = Column(Integer, ForeignKey('habits.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    completed = Column(Boolean, nullable=False, default=True)
    notes = Column(String, nullable=True)

    habit = relationship('Habit', back_populates='completions')


class WorkoutProgram(Base):
    """Programa de entrenamiento dentro de un Plan (scaffold)."""

    __tablename__ = 'workout_programs'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, unique=True)
    name = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

    plan = relationship('Plan', back_populates='workout_program')
    days = relationship('WorkoutDay', back_populates='program', cascade='all, delete-orphan')


class WorkoutDay(Base):
    __tablename__ = 'workout_days'

    id = Column(Integer, primary_key=True, index=True)
    program_id = Column(Integer, ForeignKey('workout_programs.id', ondelete='CASCADE'), nullable=False)
    week_number = Column(Integer, nullable=False, default=1)
    day_of_week = Column(Integer, nullable=False)  # 1=Mon .. 7=Sun
    name = Column(String, nullable=False)  # Push, Pull, Legs...
    notes = Column(Text, nullable=True)

    program = relationship('WorkoutProgram', back_populates='days')
    exercises = relationship('WorkoutExercise', back_populates='day', cascade='all, delete-orphan')


class WorkoutExercise(Base):
    __tablename__ = 'workout_exercises'

    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey('workout_days.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    sets = Column(Integer, nullable=True)
    reps = Column(String, nullable=True)  # "8-12" or "10"
    rest_seconds = Column(Integer, nullable=True)
    order_index = Column(Integer, nullable=False, default=0)
    progression_notes = Column(String, nullable=True)

    day = relationship('WorkoutDay', back_populates='exercises')


class DailyTask(Base):
    """Ítem del planner diario (checklist unificado / proyección TODAY)."""

    __tablename__ = 'daily_tasks'
    __table_args__ = (
        UniqueConstraint('plan_id', 'date', 'title', 'task_type', name='uq_daily_tasks_plan_date_title_type'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    title = Column(String, nullable=False)
    task_type = Column(String, nullable=False)  # habit | meal | workout | custom
    source_id = Column(Integer, nullable=True)  # habit_id / meal_id / workout_day_id / plan_task_id
    plan_task_id = Column(Integer, ForeignKey('plan_tasks.id', ondelete='SET NULL'), nullable=True)
    block_type = Column(String, nullable=True)  # high_performance | execution | recovery
    estimated_duration_minutes = Column(Integer, nullable=True)
    scheduled_time = Column(DateTime, nullable=True)
    completed = Column(Boolean, nullable=False, default=False)
    order_index = Column(Integer, nullable=False, default=0)

    plan = relationship('Plan', back_populates='daily_tasks')


class ProgressEntry(Base):
    """Registro de progreso del Plan."""

    __tablename__ = 'progress_entries'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    weight_kg = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    adherence_percent = Column(Float, nullable=True)

    plan = relationship('Plan', back_populates='progress_entries')
