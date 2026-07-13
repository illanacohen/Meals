"""Pillar data access."""

from sqlalchemy.orm import Session

from app.models.plan import Pillar


def list_pillars(db: Session, plan_id: int, enabled_only: bool = False) -> list[Pillar]:
    query = db.query(Pillar).filter(Pillar.plan_id == plan_id)
    if enabled_only:
        query = query.filter(Pillar.enabled.is_(True))
    return query.order_by(Pillar.display_order.asc(), Pillar.id.asc()).all()


def get_pillar(db: Session, plan_id: int, pillar_id: int) -> Pillar | None:
    return (
        db.query(Pillar)
        .filter(Pillar.id == pillar_id, Pillar.plan_id == plan_id)
        .first()
    )


def create_pillar(db: Session, plan_id: int, **fields) -> Pillar:
    pillar = Pillar(plan_id=plan_id, **fields)
    db.add(pillar)
    db.flush()
    return pillar
