"""Plan repository helpers."""

from sqlalchemy.orm import Session, joinedload

from app.models.plan import Plan


def get_plan_with_habits(db: Session, plan_id: int) -> Plan | None:
    return (
        db.query(Plan)
        .options(joinedload(Plan.habits))
        .filter(Plan.id == plan_id)
        .first()
    )


def list_plans(db: Session, status: str | None = None) -> list[Plan]:
    query = db.query(Plan).options(joinedload(Plan.habits)).order_by(Plan.start_date.desc())
    if status:
        query = query.filter(Plan.status == status)
    return query.all()
