from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.database import get_db
from app.models.meal import DailyGoal as DailyGoalModel
from app.models.meal import DEFAULT_SLOT_LABELS
from app.models.meal import Meal as MealModel
from app.models.meal import MealItem as MealItemModel
from app.models.meal import MealPlan as MealPlanModel
from app.models.meal import MealSlot as MealSlotModel
from app.schemas.meal import DailyGoalResponse
from app.schemas.meal import ErrorResponse
from app.schemas.meal import MacroTotals
from app.schemas.meal import MealCreate as MealCreateSchema
from app.schemas.meal import MealPlanCreate
from app.schemas.meal import MealPlanResponse
from app.schemas.meal import MealPlanSummary
from app.schemas.meal import MealResponse as MealResponseSchema
from app.services.macro_engine import calculate_daily_totals, calculate_remaining

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Resource not found',
        'model': ErrorResponse,
    },
}


def _plan_load_options():
    return (
        joinedload(MealPlanModel.slots)
        .joinedload(MealSlotModel.meals)
        .joinedload(MealModel.items)
    )


def _get_plan_or_404(plan_id: int, db: Session) -> MealPlanModel:
    plan = (
        db.query(MealPlanModel)
        .options(_plan_load_options())
        .filter(MealPlanModel.id == plan_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal plan not found')
    return plan


@router.post('/', response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
def create_meal_plan(plan: MealPlanCreate, db: Session = Depends(get_db)):
    existing = db.query(MealPlanModel).filter(MealPlanModel.date == plan.date).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Meal plan already exists for {plan.date}',
        )

    plan_db = MealPlanModel(date=plan.date, name=plan.name)
    plan_db.slots = [
        MealSlotModel(position=position, label=label)
        for position, label in DEFAULT_SLOT_LABELS
    ]
    db.add(plan_db)
    db.commit()
    return _get_plan_or_404(plan_db.id, db)


@router.get('/', response_model=list[MealPlanResponse])
def list_meal_plans(db: Session = Depends(get_db)):
    return (
        db.query(MealPlanModel)
        .options(_plan_load_options())
        .order_by(MealPlanModel.date.desc())
        .all()
    )


@router.get('/by-date/{plan_date}', response_model=MealPlanResponse, responses=NOT_FOUND)
def get_meal_plan_by_date(plan_date: date, db: Session = Depends(get_db)):
    plan = (
        db.query(MealPlanModel)
        .options(_plan_load_options())
        .filter(MealPlanModel.date == plan_date)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal plan not found')
    return plan


@router.get('/{plan_id}', response_model=MealPlanResponse, responses=NOT_FOUND)
def get_meal_plan(plan_id: int, db: Session = Depends(get_db)):
    return _get_plan_or_404(plan_id, db)


@router.get('/{plan_id}/summary', response_model=MealPlanSummary, responses=NOT_FOUND)
def get_meal_plan_summary(plan_id: int, db: Session = Depends(get_db)):
    plan = _get_plan_or_404(plan_id, db)
    meals = [meal for slot in plan.slots for meal in slot.meals]
    totals = calculate_daily_totals(meals)
    goal = db.query(DailyGoalModel).filter(DailyGoalModel.date == plan.date).first()
    remaining = calculate_remaining(goal, totals) if goal else None
    return MealPlanSummary(
        plan=plan,
        totals=MacroTotals(**totals),
        goal=goal,
        remaining=MacroTotals(**remaining) if remaining else None,
    )


@router.post(
    '/{plan_id}/slots/{position}/meals',
    response_model=MealResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def add_meal_to_slot(
    plan_id: int,
    position: int,
    meal: MealCreateSchema,
    db: Session = Depends(get_db),
):
    if position not in (1, 2, 3, 4):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Slot position must be between 1 and 4',
        )

    plan = _get_plan_or_404(plan_id, db)
    slot = next((s for s in plan.slots if s.position == position), None)
    if not slot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal slot not found')

    meal_data = meal.model_dump(exclude={'slot_id', 'items'})
    meal_db = MealModel(**meal_data, slot_id=slot.id)
    meal_db.items = [
        MealItemModel(name=item.name, grams=item.grams)
        for item in meal.items
    ]
    db.add(meal_db)
    db.commit()
    db.refresh(meal_db)
    return (
        db.query(MealModel)
        .options(joinedload(MealModel.items))
        .filter(MealModel.id == meal_db.id)
        .first()
    )

@router.delete('/{plan_id}', status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_meal_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(MealPlanModel).filter(MealPlanModel.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal plan not found')
    db.delete(plan)
    db.commit()
