from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class PlanGoalType(str, Enum):
    deficit = 'deficit'
    surplus = 'surplus'
    maintenance = 'maintenance'
    performance = 'performance'
    custom = 'custom'


class PlanStatus(str, Enum):
    draft = 'draft'
    active = 'active'
    paused = 'paused'
    completed = 'completed'


class PlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    goal_type: PlanGoalType
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = Field(default=None, ge=1, le=104)
    status: PlanStatus = PlanStatus.draft
    strategy_notes: Optional[str] = None

    @model_validator(mode='after')
    def fill_end_date(self):
        if self.end_date is None and self.duration_weeks:
            from datetime import timedelta
            self.end_date = self.start_date + timedelta(weeks=self.duration_weeks)
        if self.end_date is not None and self.end_date < self.start_date:
            raise ValueError('end_date must be >= start_date')
        return self


class PlanUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    goal_type: Optional[PlanGoalType] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = Field(default=None, ge=1, le=104)
    status: Optional[PlanStatus] = None
    strategy_notes: Optional[str] = None


class HabitCreate(BaseModel):
    name: str
    category: Optional[str] = None
    frequency: str = 'daily'
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    time_of_day: Optional[str] = 'anytime'
    difficulty: Optional[str] = 'medium'


class HabitResponse(BaseModel):
    id: int
    plan_id: int
    name: str
    category: Optional[str] = None
    frequency: str
    target_value: Optional[float] = None
    target_unit: Optional[str] = None
    time_of_day: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: bool

    model_config = {'from_attributes': True}


class PlanResponse(BaseModel):
    id: int
    name: str
    goal_type: PlanGoalType
    description: Optional[str] = None
    start_date: date
    end_date: Optional[date] = None
    duration_weeks: Optional[int] = None
    status: PlanStatus
    strategy_notes: Optional[str] = None
    user_profile_id: Optional[int] = None
    created_at: Optional[datetime] = None
    habits: list[HabitResponse] = Field(default_factory=list)

    model_config = {'from_attributes': True}


class DailyTaskResponse(BaseModel):
    id: int
    plan_id: int
    date: date
    title: str
    task_type: str
    source_id: Optional[int] = None
    plan_task_id: Optional[int] = None
    block_type: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None
    scheduled_time: Optional[datetime] = None
    completed: bool
    order_index: int

    model_config = {'from_attributes': True}


class DayBlockResponse(BaseModel):
    type: str
    starts_at: datetime
    ends_at: datetime
    tasks: list[DailyTaskResponse] = Field(default_factory=list)


class DailyPlannerResponse(BaseModel):
    plan_id: int
    date: date
    blocks: list[DayBlockResponse]
    tasks: list[DailyTaskResponse] = Field(default_factory=list)
    completed_count: int
    total_count: int


class DailyTaskToggle(BaseModel):
    completed: bool = True


class ProgressCreate(BaseModel):
    date: date
    weight_kg: Optional[float] = Field(default=None, gt=0, le=400)
    notes: Optional[str] = None
    adherence_percent: Optional[float] = Field(default=None, ge=0, le=100)


class ProgressResponse(BaseModel):
    id: int
    plan_id: int
    date: date
    weight_kg: Optional[float] = None
    notes: Optional[str] = None
    adherence_percent: Optional[float] = None

    model_config = {'from_attributes': True}
