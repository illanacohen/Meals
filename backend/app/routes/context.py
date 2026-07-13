"""UserContext API — canonical execution context for the platform."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.context import UserContextResponse, UserContextUpdate
from app.schemas.meal import ErrorResponse
from app.services.context import ContextValidationError, context_service

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'UserContext not found',
        'model': ErrorResponse,
    },
}


@router.get('/', response_model=UserContextResponse)
def get_context(db: Session = Depends(get_db)):
    """Return the complete execution context (build/seed if missing)."""
    ctx = context_service.get_or_build(db)
    db.commit()
    db.refresh(ctx)
    return ctx


@router.patch('/', response_model=UserContextResponse, responses=NOT_FOUND)
def patch_context(payload: UserContextUpdate, db: Session = Depends(get_db)):
    """Partial update of the execution context (manual settings producer)."""
    data = payload.model_dump(exclude_unset=True)
    try:
        ctx = context_service.update(db, data)
    except ContextValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    db.commit()
    db.refresh(ctx)
    return ctx
