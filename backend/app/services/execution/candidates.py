"""Candidates emitted into the Execution Engine (unified actionable units)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.context import UserContext


ENTITY_TO_LEGACY_TYPE = {
    'habit': 'habit',
    'meal_slot': 'meal',
    'workout_day': 'workout',
    'plan_task': 'custom',
    'execution_item': 'custom',
    'dynamic': 'custom',
}


@dataclass
class ExecutionContext:
    """Runtime hints for modules — derived from Plan + UserContext + date.

    Modules must not load onboarding/profile tables; they read this context only.
    """

    delay_first_meal: bool = False
    training_hour: time | None = None
    user_context: UserContext | None = None


@dataclass
class ExecutionCandidate:
    """Unit of work for TODAY. Modules emit these; the engine only places them."""

    title: str
    pillar_id: int | None
    source_module: str
    source_entity: str
    source_id: int | None
    priority: int = 3
    friction: int = 3
    duration_minutes: int = 5
    preferred_block: str = 'any'
    forbidden_blocks: list[str] = field(default_factory=list)
    force_block: str | None = None
    plan_task_id: int | None = None
    execution_item_id: int | None = None
    dynamic_execution_item_id: int | None = None
    completed: bool = False
    category: str | None = None

    @property
    def legacy_task_type(self) -> str:
        return ENTITY_TO_LEGACY_TYPE.get(self.source_entity, self.source_entity or 'custom')
