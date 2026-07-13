"""Recurrence evaluation for ExecutionItems."""

from __future__ import annotations

from datetime import date


def matches_recurrence(recurrence_rule: str | None, day: date) -> bool:
    rule = (recurrence_rule or 'daily').strip().lower()
    if rule in ('daily', 'every_day', '*'):
        return True
    if rule == 'weekdays':
        return day.weekday() < 5
    if rule == 'weekends':
        return day.weekday() >= 5
    if rule.startswith('weekly:'):
        # weekly:1,3,5  (Mon=1 … Sun=7)
        parts = rule.split(':', 1)[1]
        days = {int(p.strip()) for p in parts.split(',') if p.strip().isdigit()}
        return (day.weekday() + 1) in days
    if rule == 'once':
        return True  # visibility gated by schedule_rule / metadata start date if present
    return True
