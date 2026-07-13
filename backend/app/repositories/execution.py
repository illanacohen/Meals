"""Repositories for Plan-centric execution entities."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.execution import DynamicExecutionItem, ExecutionItem, PlanProposal


def list_execution_items(
    db: Session,
    plan_id: int,
    *,
    active_only: bool = False,
) -> list[ExecutionItem]:
    q = db.query(ExecutionItem).filter(ExecutionItem.plan_id == plan_id)
    if active_only:
        q = q.filter(ExecutionItem.active.is_(True))
    return q.order_by(ExecutionItem.priority.desc(), ExecutionItem.id.asc()).all()


def get_execution_item(db: Session, plan_id: int, item_id: int) -> ExecutionItem | None:
    return (
        db.query(ExecutionItem)
        .filter(ExecutionItem.id == item_id, ExecutionItem.plan_id == plan_id)
        .first()
    )


def create_execution_item(db: Session, plan_id: int, **fields) -> ExecutionItem:
    metadata = fields.pop('metadata', None)
    item = ExecutionItem(plan_id=plan_id, item_metadata=metadata, **fields)
    db.add(item)
    db.flush()
    return item


def list_dynamic_items(db: Session, plan_id: int) -> list[DynamicExecutionItem]:
    return (
        db.query(DynamicExecutionItem)
        .filter(DynamicExecutionItem.plan_id == plan_id)
        .order_by(DynamicExecutionItem.due_date.asc(), DynamicExecutionItem.id.asc())
        .all()
    )


def get_dynamic_item(db: Session, plan_id: int, item_id: int) -> DynamicExecutionItem | None:
    return (
        db.query(DynamicExecutionItem)
        .filter(DynamicExecutionItem.id == item_id, DynamicExecutionItem.plan_id == plan_id)
        .first()
    )


def create_dynamic_item(db: Session, plan_id: int, **fields) -> DynamicExecutionItem:
    item = DynamicExecutionItem(plan_id=plan_id, **fields)
    db.add(item)
    db.flush()
    return item


def list_proposals(db: Session, plan_id: int) -> list[PlanProposal]:
    return (
        db.query(PlanProposal)
        .filter(PlanProposal.plan_id == plan_id)
        .order_by(PlanProposal.created_at.desc())
        .all()
    )


def get_proposal(db: Session, plan_id: int, proposal_id: int) -> PlanProposal | None:
    return (
        db.query(PlanProposal)
        .filter(PlanProposal.id == proposal_id, PlanProposal.plan_id == plan_id)
        .first()
    )


def create_proposal(db: Session, plan_id: int, **fields) -> PlanProposal:
    proposal = PlanProposal(plan_id=plan_id, **fields)
    db.add(proposal)
    db.flush()
    return proposal
