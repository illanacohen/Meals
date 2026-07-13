"""Contributor registry — new life modules plug in without changing the engine."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from sqlalchemy.orm import Session

from app.models.plan import Plan
from app.services.execution.candidates import ExecutionCandidate, ExecutionContext

ContributorFn = Callable[
    [Session, Plan, date, ExecutionContext],
    list[ExecutionCandidate],
]

_REGISTRY: list[tuple[str, ContributorFn]] = []


def register_contributor(module_name: str) -> Callable[[ContributorFn], ContributorFn]:
    """Decorator: register a module that contributes ExecutionCandidates."""

    def decorator(fn: ContributorFn) -> ContributorFn:
        # Replace if re-registered (tests / reload)
        _REGISTRY[:] = [(n, f) for n, f in _REGISTRY if n != module_name]
        _REGISTRY.append((module_name, fn))
        return fn

    return decorator


def list_contributors() -> list[str]:
    return [name for name, _ in _REGISTRY]


def collect_candidates(
    db: Session,
    plan: Plan,
    day: date,
    ctx: ExecutionContext,
) -> list[ExecutionCandidate]:
    out: list[ExecutionCandidate] = []
    for _name, fn in _REGISTRY:
        out.extend(fn(db, plan, day, ctx))
    return out
