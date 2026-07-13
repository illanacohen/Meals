from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base

DEFAULT_SLOT_LABELS = (
    (1, 'Desayuno'),
    (2, 'Almuerzo'),
    (3, 'Merienda'),
    (4, 'Cena'),
)


class DailyGoal(Base):
    __tablename__ = 'daily_goals'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)


class MealPlan(Base):
    __tablename__ = 'meal_plans'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, unique=True, index=True)
    name = Column(String, nullable=True)
    goal_plan_id = Column(
        Integer,
        ForeignKey('plans.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    pillar_id = Column(Integer, ForeignKey('pillars.id', ondelete='SET NULL'), nullable=True, index=True)

    slots = relationship(
        'MealSlot',
        back_populates='plan',
        cascade='all, delete-orphan',
        order_by='MealSlot.position',
    )
    pillar = relationship('Pillar')


class MealSlot(Base):
    __tablename__ = 'meal_slots'
    __table_args__ = (
        UniqueConstraint('plan_id', 'position', name='uq_meal_slots_plan_position'),
    )

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('meal_plans.id', ondelete='CASCADE'), nullable=False)
    position = Column(Integer, nullable=False)
    label = Column(String, nullable=False)

    plan = relationship('MealPlan', back_populates='slots')
    meals = relationship('Meal', back_populates='slot')


class Meal(Base):
    __tablename__ = 'meals'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
    slot_id = Column(Integer, ForeignKey('meal_slots.id', ondelete='SET NULL'), nullable=True)

    slot = relationship('MealSlot', back_populates='meals')
    items = relationship(
        'MealItem',
        back_populates='meal',
        cascade='all, delete-orphan',
    )


class MealItem(Base):
    __tablename__ = 'meal_items'

    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey('meals.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default='g')
    grams = Column(Float, nullable=False)

    meal = relationship('Meal', back_populates='items')


class MealTemplate(Base):
    """Saved favorite meal for one-click reuse (meal library)."""

    __tablename__ = 'meal_templates'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True, index=True)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)

    items = relationship(
        'MealTemplateItem',
        back_populates='template',
        cascade='all, delete-orphan',
    )


class MealTemplateItem(Base):
    __tablename__ = 'meal_template_items'

    id = Column(Integer, primary_key=True, index=True)
    template_id = Column(Integer, ForeignKey('meal_templates.id', ondelete='CASCADE'), nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    unit = Column(String, nullable=False, default='g')
    grams = Column(Float, nullable=False)

    template = relationship('MealTemplate', back_populates='items')
