from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.database import get_db
from app.models.meal import DailyGoal as DailyGoalModel
from app.models.meal import Meal as MealModel
from app.models.meal import MealItem as MealItemModel
from app.models.meal import MealPlan as MealPlanModel
from app.models.meal import MealSlot as MealSlotModel
from app.models.meal import MealTemplate as MealTemplateModel
from app.models.user_profile import UserProfile
from app.schemas.meal import ErrorResponse
from app.schemas.suggest import SuggestMealRequest, SuggestMealResponse
from app.services.macro_engine import calculate_daily_totals, calculate_remaining
from app.services.meal_generator import SLOT_NAMES, generate_meal_for_remaining

router = APIRouter()


def _infer_meal_name(prompt: str | None, slot_position: int, explicit: str | None) -> str | None:
    if explicit:
        return explicit
    if prompt:
        lower = prompt.lower()
        for position, label in SLOT_NAMES.items():
            if label.lower() in lower or label.lower().rstrip('a') in lower:
                return label
        if 'cena' in lower:
            return 'Cena'
        if 'desayuno' in lower:
            return 'Desayuno'
        if 'almuerzo' in lower:
            return 'Almuerzo'
        if 'merienda' in lower:
            return 'Merienda'
    return SLOT_NAMES.get(slot_position)


def _remaining_from_plan(plan_id: int, db: Session) -> dict:
    plan = (
        db.query(MealPlanModel)
        .options(
            joinedload(MealPlanModel.slots)
            .joinedload(MealSlotModel.meals)
        )
        .filter(MealPlanModel.id == plan_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal plan not found')

    goal = db.query(DailyGoalModel).filter(DailyGoalModel.date == plan.date).first()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'No daily goal found for {plan.date}',
        )

    meals = [meal for slot in plan.slots for meal in slot.meals]
    totals = calculate_daily_totals(meals)
    remaining = calculate_remaining(goal, totals)
    return {
        'calories': max(0.0, remaining['calories']),
        'protein': max(0.0, remaining['protein']),
        'fat': max(0.0, remaining['fat']),
        'carbs': max(0.0, remaining['carbs']),
        'fiber': max(0.0, remaining['fiber']),
    }


@router.post(
    '/meal',
    response_model=SuggestMealResponse,
    responses={
        status.HTTP_404_NOT_FOUND: {'model': ErrorResponse},
        status.HTTP_400_BAD_REQUEST: {'model': ErrorResponse},
    },
)
def suggest_meal(payload: SuggestMealRequest, db: Session = Depends(get_db)):
    """Build a meal from remaining macros using library + preferred foods."""
    if payload.remaining is not None:
        remaining = payload.remaining.model_dump()
    else:
        remaining = _remaining_from_plan(payload.plan_id, db)

    if remaining.get('protein', 0) <= 0 and remaining.get('carbs', 0) <= 0 and remaining.get('fat', 0) <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='No remaining macros to fill',
        )

    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    preferred = list(payload.preferred_foods or [])
    excluded = list(payload.excluded_foods or [])
    if profile:
        preferred = preferred or list(profile.food_preferences or [])
        excluded = list(dict.fromkeys(excluded + list(profile.excluded_foods or [])))

    templates = []
    if payload.use_library:
        templates = (
            db.query(MealTemplateModel)
            .options(joinedload(MealTemplateModel.items))
            .all()
        )

    meal_name = _infer_meal_name(payload.prompt, payload.slot_position, payload.meal_name)
    suggestion = generate_meal_for_remaining(
        remaining,
        meal_name=meal_name,
        preferred_foods=preferred,
        excluded_foods=excluded,
        templates=templates,
        slot_position=payload.slot_position,
    )

    saved_meal = None
    if payload.save_to_slot:
        if payload.plan_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='plan_id is required when save_to_slot is true',
            )
        plan = (
            db.query(MealPlanModel)
            .options(joinedload(MealPlanModel.slots))
            .filter(MealPlanModel.id == payload.plan_id)
            .first()
        )
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal plan not found')
        slot = next((s for s in plan.slots if s.position == payload.slot_position), None)
        if not slot:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal slot not found')

        macros = suggestion['macros']
        meal_db = MealModel(
            name=suggestion['name'],
            calories=macros['calories'],
            protein=macros['protein'],
            fat=macros['fat'],
            carbs=macros['carbs'],
            fiber=macros.get('fiber', 0),
            slot_id=slot.id,
            items=[
                MealItemModel(
                    name=item['name'],
                    quantity=item['quantity'],
                    unit=item['unit'],
                    grams=item['grams'],
                )
                for item in suggestion['items']
            ],
        )
        db.add(meal_db)
        db.commit()
        saved_meal = (
            db.query(MealModel)
            .options(joinedload(MealModel.items))
            .filter(MealModel.id == meal_db.id)
            .first()
        )

    return SuggestMealResponse(
        name=suggestion['name'],
        source=suggestion['source'],
        template_id=suggestion.get('template_id'),
        template_name=suggestion.get('template_name'),
        scale=suggestion.get('scale', 1.0),
        items=suggestion['items'],
        macros=suggestion['macros'],
        remaining_before=suggestion['remaining_before'],
        remaining_after=suggestion['remaining_after'],
        message=suggestion['message'],
        saved_meal=saved_meal,
        prompt=payload.prompt,
    )
