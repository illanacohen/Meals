"""Execution Engine package.

Plan → ExecutionItems → Engine → TODAY (projection)
DynamicExecutionItems merge into the same view.
"""

from app.services.execution.registry import list_contributors, register_contributor
from app.services.execution.service import (
    build_today,
    rebuild_today,
    registered_modules,
    toggle_today_task,
)

# Register built-in module contributors on import
from app.services.execution import modules as _modules  # noqa: F401

__all__ = [
    'build_today',
    'rebuild_today',
    'toggle_today_task',
    'registered_modules',
    'register_contributor',
    'list_contributors',
]
