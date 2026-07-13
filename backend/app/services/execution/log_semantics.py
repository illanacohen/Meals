"""Shared helpers for ExecutionLog exception semantics."""

from __future__ import annotations

from app.models.execution import EXECUTION_LOG_STATUSES


def is_valid_log_status(status: str) -> bool:
    return status in EXECUTION_LOG_STATUSES


def log_means_completed(status: str | None) -> bool:
    """Whether a log status counts as done for TODAY projection.

    No log → not marked done (silence is on-plan for friction, not a checkbox).
    skipped → not done. All other statuses → done (with optional friction signal).
    """
    if status is None:
        return False
    return status != 'skipped'
