"""Schemas for ExecutionItem, DynamicExecutionItem, PlanProposal."""

from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ExecutionItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    pillar_id: Optional[int] = None
    source_module: str = 'planner'
    recurrence_rule: str = 'daily'
    schedule_rule: Optional[dict[str, Any]] = None
    priority: int = Field(default=3, ge=1, le=5)
    estimated_duration: int = Field(default=15, ge=1, le=480)
    active: bool = True
    metadata: Optional[dict[str, Any]] = None


class ExecutionItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    pillar_id: Optional[int] = None
    source_module: Optional[str] = None
    recurrence_rule: Optional[str] = None
    schedule_rule: Optional[dict[str, Any]] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    estimated_duration: Optional[int] = Field(default=None, ge=1, le=480)
    active: Optional[bool] = None
    metadata: Optional[dict[str, Any]] = None


class ExecutionItemResponse(BaseModel):
    id: int
    plan_id: int
    pillar_id: Optional[int] = None
    source_module: str
    title: str
    description: Optional[str] = None
    recurrence_rule: str
    schedule_rule: Optional[dict[str, Any]] = None
    priority: int
    estimated_duration: int
    active: bool
    metadata: Optional[dict[str, Any]] = None
    habit_id: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = {'from_attributes': True}

    @classmethod
    def from_orm_item(cls, item: Any) -> 'ExecutionItemResponse':
        return cls(
            id=item.id,
            plan_id=item.plan_id,
            pillar_id=item.pillar_id,
            source_module=item.source_module,
            title=item.title,
            description=item.description,
            recurrence_rule=item.recurrence_rule,
            schedule_rule=item.schedule_rule,
            priority=item.priority,
            estimated_duration=item.estimated_duration,
            active=item.active,
            metadata=item.item_metadata,
            habit_id=item.habit_id,
            created_at=item.created_at,
        )


class DynamicExecutionItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    pillar_id: Optional[int] = None
    due_date: Optional[date] = None
    priority: int = Field(default=3, ge=1, le=5)
    created_by_user: bool = True


class DynamicExecutionItemUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    pillar_id: Optional[int] = None
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)


class DynamicExecutionItemResponse(BaseModel):
    id: int
    plan_id: Optional[int] = None
    pillar_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    completed: bool
    created_by_user: bool
    priority: int
    created_at: Optional[datetime] = None

    model_config = {'from_attributes': True}


class PlanProposalCreate(BaseModel):
    rationale: Optional[str] = None
    payload: dict[str, Any]
    created_by: str = 'system'


class PlanProposalUpdate(BaseModel):
    status: str  # pending | accepted | rejected


class PlanProposalResponse(BaseModel):
    id: int
    plan_id: int
    status: str
    rationale: Optional[str] = None
    payload: dict[str, Any]
    created_by: str
    created_at: Optional[datetime] = None

    model_config = {'from_attributes': True}
