"""Plan-centric execution domain: long-lived items, exception logs, proposals."""

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.db.base import Base

# Exception-driven statuses. Absence of a log for a date = neutral / on-plan.
EXECUTION_LOG_STATUSES = (
    'executed_smoothly',
    'high_friction',
    'skipped',
    'shifted_schedule',
)


class ExecutionItem(Base):
    """Long-lived action belonging to a Plan (source of truth for planned work)."""

    __tablename__ = 'execution_items'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    pillar_id = Column(Integer, ForeignKey('pillars.id', ondelete='SET NULL'), nullable=True, index=True)
    source_module = Column(String, nullable=False, default='planner')
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    recurrence_rule = Column(String, nullable=False, default='daily')  # daily | weekdays | weekly
    schedule_rule = Column(JSON, nullable=True)  # preferred_block, friction, preferred_time, etc.
    priority = Column(Integer, nullable=False, default=3)
    estimated_duration = Column(Integer, nullable=False, default=5)
    active = Column(Boolean, nullable=False, default=True)
    item_metadata = Column('metadata', JSON, nullable=True)
    habit_id = Column(Integer, ForeignKey('habits.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan = relationship('Plan', back_populates='execution_items')
    pillar = relationship('Pillar', back_populates='execution_items')
    logs = relationship(
        'ExecutionLog',
        back_populates='execution_item',
        cascade='all, delete-orphan',
    )


class ExecutionLog(Base):
    """Optional exception log for a planned item on a date.

    Users log only when something hurt, was skipped, or shifted.
    No row for a date means neutral / plan assumed running.
    """

    __tablename__ = 'execution_logs'
    __table_args__ = (
        UniqueConstraint('execution_item_id', 'date', name='uq_execution_logs_item_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    execution_item_id = Column(
        Integer,
        ForeignKey('execution_items.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    date = Column(Date, nullable=False, index=True)
    status = Column(String, nullable=False, default='executed_smoothly')
    logged_at_time = Column(Time, nullable=True)
    log_metadata = Column('metadata', JSON, nullable=True)

    execution_item = relationship('ExecutionItem', back_populates='logs')


class DynamicExecutionItem(Base):
    """Temporary / real-life task — not part of the long-term Plan catalog."""

    __tablename__ = 'dynamic_execution_items'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=True, index=True)
    pillar_id = Column(Integer, ForeignKey('pillars.id', ondelete='SET NULL'), nullable=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=True, index=True)
    completed = Column(Boolean, nullable=False, default=False)
    created_by_user = Column(Boolean, nullable=False, default=True)
    priority = Column(Integer, nullable=False, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan = relationship('Plan', back_populates='dynamic_execution_items')
    pillar = relationship('Pillar', back_populates='dynamic_items')


class PlanProposal(Base):
    """Reviewable change proposal for a Plan — never auto-applied by the engine."""

    __tablename__ = 'plan_proposals'

    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey('plans.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String, nullable=False, default='pending')  # pending | accepted | rejected
    rationale = Column(Text, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_by = Column(String, nullable=False, default='system')  # ai | system | user | friction_engine
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    plan = relationship('Plan', back_populates='plan_proposals')
