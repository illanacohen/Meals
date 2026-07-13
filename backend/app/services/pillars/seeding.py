"""Pillar resolution helpers — no hardcoded life-domain catalog."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.plan import Pillar, Plan


def get_pillar_for_plan(db: Session, plan: Plan, pillar_id: int) -> Pillar:
    """Fetch a pillar that belongs to the plan or raise ValueError."""
    pillar = (
        db.query(Pillar)
        .filter(Pillar.id == pillar_id, Pillar.plan_id == plan.id)
        .first()
    )
    if pillar is None:
        raise ValueError('Pillar not found for this plan')
    return pillar


def require_enabled_pillar(db: Session, plan: Plan, pillar_id: int) -> Pillar:
    pillar = get_pillar_for_plan(db, plan, pillar_id)
    if not pillar.enabled:
        raise ValueError('Pillar is disabled')
    return pillar
