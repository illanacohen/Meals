from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.meal import DailyGoal as DailyGoalModel
from app.models.user_profile import UserProfile
from app.schemas.meal import ErrorResponse
from app.schemas.onboarding import (
    OnboardingBasicsRequest,
    OnboardingRefineRequest,
    OnboardingRequest,
    OnboardingResponse,
    UserProfileResponse,
)
from app.services.onboarding_engine import run_onboarding_calculations

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Profile not found',
        'model': ErrorResponse,
    },
}

_PROFILE_FIELDS = (
    'age', 'gender', 'weight_kg', 'height_cm', 'goal', 'deficit_intensity', 'surplus_intensity',
    'activity_level', 'body_fat_percent', 'daily_steps', 'training_days_per_week',
    'training_type', 'training_level', 'training_time', 'training_hour', 'wake_time',
    'sleep_time', 'meals_per_day', 'hunger_pattern', 'prefers_larger_post_workout',
    'food_preferences', 'excluded_foods', 'budget_level', 'cooking_time_minutes',
)

_ENUM_KEYS = (
    'gender', 'goal', 'deficit_intensity', 'surplus_intensity', 'activity_level',
    'training_type', 'training_level', 'training_time', 'hunger_pattern', 'budget_level',
)


def _enum_val(value):
    return value.value if hasattr(value, 'value') else value


def _normalize(data: dict) -> dict:
    for key in _ENUM_KEYS:
        if data.get(key) is not None:
            data[key] = _enum_val(data[key])
    return data


def _basics_to_profile_kwargs(payload: OnboardingBasicsRequest) -> dict:
    data = payload.model_dump(exclude={'create_goal_for_today'})
    data = _normalize(data)
    # Defaults for fields not asked in step 1
    data.setdefault('activity_level', 'moderate')
    data.setdefault('training_days_per_week', 0)
    data.setdefault('meals_per_day', 4)
    data.setdefault('prefers_larger_post_workout', True)
    data.setdefault('training_time', 'none')
    data.setdefault('hunger_pattern', 'balanced')
    return data


def _full_to_profile_kwargs(payload: OnboardingRequest) -> dict:
    return _normalize(payload.model_dump(exclude={'create_goal_for_today'}))


def _apply_kwargs(profile: UserProfile, data: dict) -> None:
    for key, value in data.items():
        setattr(profile, key, value)


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


def _build_response(profile, calc, goal_id=None, message='') -> OnboardingResponse:
    return OnboardingResponse(
        profile=profile,
        bmr=calc['bmr'],
        tdee=calc['tdee'],
        targets=calc['targets'],
        distribution=calc['distribution'],
        guidance=calc['guidance'],
        goal_id=goal_id,
        message=message,
    )


def _save_and_respond(db: Session, profile: UserProfile, create_goal: bool, message: str):
    db.flush()
    # Onboarding is a producer of UserContext — never leave context stale.
    from app.services.context import context_service

    context_service.sync_from_profile(db, profile)
    calc = run_onboarding_calculations(profile)
    goal_id = None
    if create_goal:
        goal = _upsert_today_goal(db, calc['targets'])
        db.flush()
        goal_id = goal.id
        message = message + ' Daily goal for today updated.'
    db.commit()
    db.refresh(profile)
    return _build_response(profile, calc, goal_id=goal_id, message=message)


@router.post('/', response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def complete_onboarding_basics(payload: OnboardingBasicsRequest, db: Session = Depends(get_db)):
    """Paso 1 obligatorio: edad, genero, peso, altura, objetivo."""
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    _apply_kwargs(profile, _basics_to_profile_kwargs(payload))
    return _save_and_respond(
        db,
        profile,
        create_goal=payload.create_goal_for_today,
        message='Paso basico guardado. Macros calculados. Usa /onboarding/refine para horario de entreno y demas.',
    )


@router.patch('/refine', response_model=OnboardingResponse, responses=NOT_FOUND)
def refine_onboarding(payload: OnboardingRefineRequest, db: Session = Depends(get_db)):
    """Paso 2 opcional: actividad, entreno, preferencias. Redistribuye comidas por horario."""
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Complete /onboarding/ basics first',
        )

    updates = _normalize(payload.model_dump(exclude_unset=True, exclude={'create_goal_for_today'}))
    _apply_kwargs(profile, updates)
    return _save_and_respond(
        db,
        profile,
        create_goal=payload.create_goal_for_today,
        message='Perfil refinado. Distribucion reorganizada segun horario de entrenamiento.',
    )


@router.post('/full', response_model=OnboardingResponse, status_code=status.HTTP_201_CREATED)
def complete_onboarding_full(payload: OnboardingRequest, db: Session = Depends(get_db)):
    """Atajo: basicos + opcionales en un solo request."""
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        profile = UserProfile()
        db.add(profile)

    _apply_kwargs(profile, _full_to_profile_kwargs(payload))
    return _save_and_respond(
        db,
        profile,
        create_goal=payload.create_goal_for_today,
        message='Onboarding completo guardado con distribucion por horario.',
    )


@router.get('/profile', response_model=UserProfileResponse, responses=NOT_FOUND)
def get_profile(db: Session = Depends(get_db)):
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Profile not found')
    return profile


@router.post('/preview', response_model=OnboardingResponse)
def preview_onboarding_post(payload: OnboardingRequest):
    profile = UserProfile(**_full_to_profile_kwargs(payload))
    calc = run_onboarding_calculations(profile)
    preview_profile = UserProfileResponse(id=0, **{k: getattr(profile, k) for k in _PROFILE_FIELDS})
    return _build_response(
        preview_profile,
        calc,
        goal_id=None,
        message='Preview only. Nothing was saved.',
    )
