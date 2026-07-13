"""Execution-item APIs: exception logs, visual substitutes, friction analysis."""

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.execution import ExecutionItem, ExecutionLog
from app.schemas.execution import (
    ExecutionItemResponse,
    ExecutionLogCreate,
    ExecutionLogResponse,
    PlanProposalResponse,
    ReplaceRequest,
    ReplaceResponse,
    SubstituteOptionResponse,
)
from app.schemas.meal import ErrorResponse
from app.services.context import context_service
from app.services.execution.friction_engine import friction_engine
from app.services.execution.log_semantics import is_valid_log_status
from app.services.execution.substitution import substitution_service

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Not found',
        'model': ErrorResponse,
    },
}


def _get_item_or_404(item_id: int, db: Session) -> ExecutionItem:
    item = db.get(ExecutionItem, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ExecutionItem not found')
    return item


@router.post(
    '/friction/analyze',
    response_model=list[PlanProposalResponse],
    status_code=status.HTTP_201_CREATED,
)
def analyze_friction(
    user_id: int | None = Query(
        default=None,
        description='UserContext.user_id, context id, or profile id',
    ),
    as_of: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Run FrictionEngine; creates pending PlanProposal records (no chat text)."""
    ctx = context_service.get_or_build(db)
    resolved = user_id
    if resolved is None:
        resolved = ctx.user_id or ctx.id or ctx.user_profile_id
    if resolved is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No UserContext identity available for friction analysis',
        )
    proposals = friction_engine.analyze_friction_patterns(db, resolved, as_of=as_of)
    db.commit()
    for proposal in proposals:
        db.refresh(proposal)
    return proposals


@router.get(
    '/{item_id}/logs',
    response_model=list[ExecutionLogResponse],
    responses=NOT_FOUND,
)
def list_execution_logs(
    item_id: int,
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    _get_item_or_404(item_id, db)
    q = db.query(ExecutionLog).filter(ExecutionLog.execution_item_id == item_id)
    if date_from is not None:
        q = q.filter(ExecutionLog.date >= date_from)
    if date_to is not None:
        q = q.filter(ExecutionLog.date <= date_to)
    logs = q.order_by(ExecutionLog.date.desc(), ExecutionLog.id.desc()).all()
    return [ExecutionLogResponse.from_orm_log(log) for log in logs]


@router.post(
    '/{item_id}/logs',
    response_model=ExecutionLogResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_execution_log(
    item_id: int,
    payload: ExecutionLogCreate,
    db: Session = Depends(get_db),
):
    """Log by exception — skipped, high friction, or shifted schedule."""
    _get_item_or_404(item_id, db)
    if not is_valid_log_status(payload.status):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail='Invalid status')

    existing = (
        db.query(ExecutionLog)
        .filter(ExecutionLog.execution_item_id == item_id, ExecutionLog.date == payload.date)
        .first()
    )
    if existing is None:
        log = ExecutionLog(
            execution_item_id=item_id,
            date=payload.date,
            status=payload.status,
            logged_at_time=payload.logged_at_time,
            log_metadata=payload.metadata,
        )
        db.add(log)
    else:
        existing.status = payload.status
        existing.logged_at_time = payload.logged_at_time
        existing.log_metadata = payload.metadata
        log = existing

    db.commit()
    db.refresh(log)
    return ExecutionLogResponse.from_orm_log(log)


@router.get(
    '/{item_id}/alternatives',
    response_model=list[SubstituteOptionResponse],
    responses=NOT_FOUND,
)
def get_alternatives(item_id: int, db: Session = Depends(get_db)):
    """Visual Replace cards — structural substitutes matching macros/constraints."""
    _get_item_or_404(item_id, db)
    ctx = context_service.get(db)
    try:
        options = substitution_service.get_smart_substitutes(db, item_id, ctx, limit=3)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [
        SubstituteOptionResponse(
            id=o.id,
            title=o.title,
            source_module=o.source_module,
            metadata=o.metadata,
            match_score=o.match_score,
            reason=o.reason,
        )
        for o in options
    ]


@router.post(
    '/{item_id}/replace',
    response_model=ReplaceResponse,
    responses=NOT_FOUND,
)
def replace_execution_item(
    item_id: int,
    payload: ReplaceRequest,
    db: Session = Depends(get_db),
):
    """Apply a chosen visual substitute (mutates item) or queue a PlanProposal."""
    _get_item_or_404(item_id, db)
    ctx = context_service.get(db)
    try:
        item, proposal = substitution_service.apply_substitute(
            db,
            item_id,
            payload.alternative_id,
            ctx,
            as_proposal=payload.as_proposal,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    db.commit()
    db.refresh(item)
    db.refresh(proposal)
    return ReplaceResponse(
        item=ExecutionItemResponse.from_orm_item(item),
        proposal=PlanProposalResponse.model_validate(proposal),
    )
