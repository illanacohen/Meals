from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database.database import get_db
from app.models.meal import Meal as MealModel
from app.models.meal import MealPlan as MealPlanModel
from app.models.meal import MealSlot as MealSlotModel
from app.schemas.meal import ErrorResponse
from app.schemas.shopping import ShoppingListResponse
from app.services.shopping_list import build_shopping_list, collect_items_from_plans

router = APIRouter()


def _load_plans_in_range(db: Session, start: date, end: date) -> list[MealPlanModel]:
    return (
        db.query(MealPlanModel)
        .options(
            joinedload(MealPlanModel.slots)
            .joinedload(MealSlotModel.meals)
            .joinedload(MealModel.items)
        )
        .filter(MealPlanModel.date >= start, MealPlanModel.date <= end)
        .order_by(MealPlanModel.date.asc())
        .all()
    )


@router.get(
    '/',
    response_model=ShoppingListResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {'model': ErrorResponse},
    },
)
def get_shopping_list(
    start_date: date = Query(..., description='First day of the range (inclusive)'),
    end_date: date | None = Query(
        default=None,
        description='Last day (inclusive). Defaults to start_date + 6 days (week).',
    ),
    db: Session = Depends(get_db),
):
    """Aggregate all meal ingredients in a date range into one shopping list."""
    if end_date is None:
        end_date = start_date + timedelta(days=6)

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='end_date must be >= start_date',
        )

    plans = _load_plans_in_range(db, start_date, end_date)
    raw_items = collect_items_from_plans(plans)
    lines = build_shopping_list(raw_items)

    plan_ids = [p.id for p in plans]
    display_lines = [row['display'] for row in lines]
    if plans:
        message = (
            f'Shopping list for {len(plans)} plan(s) '
            f'from {start_date} to {end_date}: {len(lines)} item(s).'
        )
    else:
        message = f'No meal plans found between {start_date} and {end_date}.'

    return ShoppingListResponse(
        start_date=start_date,
        end_date=end_date,
        plan_ids=plan_ids,
        plan_count=len(plans),
        item_count=len(lines),
        items=lines,
        lines=display_lines,
        message=message,
    )


@router.get(
    '/week',
    response_model=ShoppingListResponse,
    responses={status.HTTP_400_BAD_REQUEST: {'model': ErrorResponse}},
)
def get_weekly_shopping_list(
    week_start: date = Query(..., description='Monday (or any start) of the week'),
    db: Session = Depends(get_db),
):
    """Shortcut: shopping list for week_start .. week_start+6."""
    return get_shopping_list(
        start_date=week_start,
        end_date=week_start + timedelta(days=6),
        db=db,
    )
