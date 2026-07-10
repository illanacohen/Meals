from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.meal import DailyGoal as DailyGoalModel
from app.models.user_profile import UserProfile
from app.schemas.meal import ErrorResponse
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse, UserProfileResponse
from app.services.onboarding_engine import run_onboarding_calculations

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Profile not found',
        'model': ErrorResponse,
    },
}


def _enum_val(value):
    return value.value if hasattr(value, 'value') else value


def _apply_request_to_profile(profile: UserProfile, payload: OnboardingRequest) -> None:
    profile.age = payload.age
    profile.sex = _enum_val(payload.sex)
    profile.weight_kg = payload.weight_kg
    profile.height_cm = payload.height_cm
    profile.goal = _enum_val(payload.goal)
    profile.deficit_intensity = _enum_val(payload.deficit_intensity) if payload.deficit_intensity else None
    profile.surplus_intensity = _enum_val(payload.surplus_intensity) if payload.surplus_intensity else None
    profile.activity_level = _enum_val(payload.activity_level)
    profile.training_days_per_week = payload.training_days_per_week
    profile.training_time = _enum_val(payload.training_time) if payload.training_time else None
    profile.wake_time = payload.wake_time
    profile.sleep_time = payload.sleep_time
    profile.meals_per_day = payload.meals_per_day
    profile.hunger_pattern = _enum_val(payload.hunger_pattern) if payload.hunger_pattern else None
    profile.prefers_larger_post_workout = payload.prefers_larger_post_workout


def _upsert_today_goal(db: Session, targets: dict) -> DailyGoalModel:
    today = date.today()
    goal = db.query(DailyGoalModel).filter(DailyGoalModel.date == today).first()
    if not goal:
        goal = DailyGoalModel(date=today)
        db.add(goal)
    goal.calories = targets['calories']
    goal.protein = targets['protein']
    goal.fat = targets['fat']
    goal.carbs = targets['carbs']
    goal.fiber = targets['fiber']
    return goal


@router.post('/', response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def complete_onboarding(payload: OnboardingRequest, db: Session = Depends(get_db)):
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    _apply_request_to_profile(profile, payload)
    db.flush()

    calc = run_onboarding_calculations(profile)
    goal_id = None
    message = 'Onboarding saved. Targets and meal distribution calculated.'

    if payload.create_goal_for_today:
        goal = _upsert_today_goal(db, calc['targets'])
        db.flush()
        goal_id = goal.id
        message = (
            'Onboarding saved. Daily goal for today was created/updated from your targets.'
        )

    db.commit()
    db.refresh(profile)

    return OnboardingResponse(
        profile=profile,
        bmr=calc['bmr'],
        tdee=calc['tdee'],
        targets=calc['targets'],
        distribution=calc['distribution'],
        goal_id=goal_id,
        message=message,
    )


@router.get('/profile', response_model=UserProfileResponse, responses=NOT_FOUND)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Profile not found')
    return profile


@router.post('/preview', response_model=OnboardingResponse)
def preview_onboarding_post(payload: OnboardingRequest):
    profile = UserProfile(
        age=payload.age,
        sex=_enum_val(payload.sex),
        weight_kg=payload.weight_kg,
        height_cm=payload.height_cm,
        goal=_enum_val(payload.goal),
        deficit_intensity=_enum_val(payload.deficit_intensity) if payload.deficit_intensity else None,
        surplus_intensity=_enum_val(payload.surplus_intensity) if payload.surplus_intensity else None,
        activity_level=_enum_val(payload.activity_level),
        training_days_per_week=payload.training_days_per_week,
        training_time=_enum_val(payload.training_time) if payload.training_time else None,
        wake_time=payload.wake_time,
        sleep_time=payload.sleep_time,
        meals_per_day=payload.meals_per_day,
        hunger_pattern=_enum_val(payload.hunger_pattern) if payload.hunger_pattern else None,
        prefers_larger_post_workout=payload.prefers_larger_post_workout,
    )
    calc = run_onboarding_calculations(profile)
    return OnboardingResponse(
        profile=UserProfileResponse(
            id=0,
            age=profile.age,
            sex=profile.sex,
            weight_kg=profile.weight_kg,
            height_cm=profile.height_cm,
            goal=profile.goal,
            deficit_intensity=profile.deficit_intensity,
            surplus_intensity=profile.surplus_intensity,
            activity_level=profile.activity_level,
            training_days_per_week=profile.training_days_per_week,
            training_time=profile.training_time,
            wake_time=profile.wake_time,
            sleep_time=profile.sleep_time,
            meals_per_day=profile.meals_per_day,
            hunger_pattern=profile.hunger_pattern,
            prefers_larger_post_workout=profile.prefers_larger_post_workout,
        ),
        bmr=calc['bmr'],
        tdee=calc['tdee'],
        targets=calc['targets'],
        distribution=calc['distribution'],
        goal_id=None,
        message='Preview only. Nothing was saved.',
    )
