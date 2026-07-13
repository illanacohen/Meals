"""ContextService — build, update, validate, and expose UserContext.

Onboarding and other producers write through this service.
The Execution Engine and future domains consume only via this service.
"""

from __future__ import annotations

from datetime import time

from sqlalchemy.orm import Session

from app.models.context import UserContext
from app.models.plan import Plan
from app.models.planner import DaySchedulePolicy
from app.models.user_profile import UserProfile

DEFAULT_WAKE = time(7, 0)
DEFAULT_SLEEP = time(23, 0)
DEFAULT_TIMEZONE = 'UTC'

_MUTABLE_FIELDS = (
    'age',
    'sex',
    'height_cm',
    'weight_kg',
    'wake_time',
    'sleep_time',
    'working_hours',
    'preferred_training_time',
    'preferred_meal_times',
    'timezone',
    'preferences',
    'favorite_foods',
    'disliked_foods',
    'preferred_training_style',
    'preferred_learning_style',
    'dietary_restrictions',
    'food_intolerances',
    'equipment',
    'injuries',
    'mobility_limitations',
    'budget',
    'available_time',
    'gym_access',
    'work_schedule_constraints',
    'energy_profile',
    'motivation_style',
    'discipline_level',
    'planning_style',
    'notification_preferences',
    'current_streaks',
    'completed_habits',
    'adherence_score',
)


class ContextValidationError(ValueError):
    """Raised when UserContext fails consistency checks."""


class ContextService:
    """Canonical access to the UserContext aggregate."""

    def get(self, db: Session) -> UserContext | None:
        """Return the single-tenant context row (first / only), if any."""
        return db.query(UserContext).order_by(UserContext.id.asc()).first()

    def get_or_build(self, db: Session, plan: Plan | None = None) -> UserContext:
        """
        Load UserContext, creating/seeding from onboarding producers if missing.

        Always returns a persisted row so the engine has a stable aggregate.
        """
        ctx = self._resolve_existing(db, plan)
        if ctx is not None:
            return ctx
        return self.build(db, plan=plan)

    def load_for_execution(self, db: Session, plan: Plan) -> UserContext:
        """Execution Engine entry point — never reads onboarding tables itself."""
        return self.get_or_build(db, plan=plan)

    def build(self, db: Session, plan: Plan | None = None) -> UserContext:
        """Create UserContext from current producers (profile + schedule policy)."""
        profile = self._resolve_profile(db, plan)
        policy = self._resolve_policy(db, profile)

        ctx = UserContext(user_profile_id=profile.id if profile else None)
        self._apply_producer_snapshot(ctx, profile, policy)
        self.validate(ctx)
        db.add(ctx)
        db.flush()
        return ctx

    def sync_from_profile(self, db: Session, profile: UserProfile) -> UserContext:
        """
        Onboarding producer: upsert UserContext from a saved UserProfile.

        Does not wipe fields that onboarding does not own (equipment, injuries, …)
        unless the profile explicitly carries a mapped value.
        """
        ctx = (
            db.query(UserContext)
            .filter(UserContext.user_profile_id == profile.id)
            .first()
        )
        if ctx is None:
            ctx = self.get(db)
            if ctx is not None and ctx.user_profile_id is None:
                ctx.user_profile_id = profile.id
            else:
                ctx = UserContext(user_profile_id=profile.id)
                db.add(ctx)

        policy = self._resolve_policy(db, profile)
        self._apply_producer_snapshot(ctx, profile, policy, overwrite_owned=True)
        self.validate(ctx)
        db.flush()
        return ctx

    def update(self, db: Session, data: dict) -> UserContext:
        """Apply a partial update (settings / manual producer)."""
        ctx = self.get_or_build(db)
        for key, value in data.items():
            if key not in _MUTABLE_FIELDS:
                continue
            setattr(ctx, key, value)
        self.validate(ctx)
        db.flush()
        return ctx

    def validate(self, ctx: UserContext) -> None:
        """Lightweight consistency checks for the aggregate."""
        if ctx.age is not None and not (1 <= ctx.age <= 120):
            raise ContextValidationError('age must be between 1 and 120')
        if ctx.height_cm is not None and not (0 < ctx.height_cm <= 300):
            raise ContextValidationError('height_cm out of range')
        if ctx.weight_kg is not None and not (0 < ctx.weight_kg <= 500):
            raise ContextValidationError('weight_kg out of range')
        if ctx.adherence_score is not None and not (0 <= ctx.adherence_score <= 100):
            raise ContextValidationError('adherence_score must be 0–100')
        if ctx.available_time is not None and not (0 <= ctx.available_time <= 1440):
            raise ContextValidationError('available_time must be 0–1440 minutes')
        if ctx.wake_time and ctx.sleep_time and ctx.wake_time == ctx.sleep_time:
            raise ContextValidationError('wake_time and sleep_time must differ')

    # --- internals ---

    def _resolve_existing(self, db: Session, plan: Plan | None) -> UserContext | None:
        if plan and plan.user_profile_id:
            ctx = (
                db.query(UserContext)
                .filter(UserContext.user_profile_id == plan.user_profile_id)
                .first()
            )
            if ctx is not None:
                return ctx
        return self.get(db)

    def _resolve_profile(self, db: Session, plan: Plan | None) -> UserProfile | None:
        if plan and plan.user_profile_id:
            profile = db.query(UserProfile).filter(UserProfile.id == plan.user_profile_id).first()
            if profile is not None:
                return profile
        return db.query(UserProfile).order_by(UserProfile.id.asc()).first()

    def _resolve_policy(self, db: Session, profile: UserProfile | None) -> DaySchedulePolicy | None:
        if profile is None:
            return (
                db.query(DaySchedulePolicy)
                .filter(DaySchedulePolicy.user_profile_id.is_(None))
                .first()
            )
        return (
            db.query(DaySchedulePolicy)
            .filter(DaySchedulePolicy.user_profile_id == profile.id)
            .first()
        )

    def _apply_producer_snapshot(
        self,
        ctx: UserContext,
        profile: UserProfile | None,
        policy: DaySchedulePolicy | None,
        *,
        overwrite_owned: bool = True,
    ) -> None:
        """Map known producers into the aggregate."""
        if profile is not None and overwrite_owned:
            ctx.age = profile.age
            ctx.sex = profile.gender
            ctx.height_cm = profile.height_cm
            ctx.weight_kg = profile.weight_kg
            ctx.wake_time = profile.wake_time or ctx.wake_time
            ctx.sleep_time = profile.sleep_time or ctx.sleep_time
            ctx.preferred_training_time = profile.training_hour or ctx.preferred_training_time
            ctx.preferred_training_style = profile.training_type or ctx.preferred_training_style
            ctx.favorite_foods = profile.food_preferences
            ctx.disliked_foods = profile.excluded_foods
            ctx.budget = profile.budget_level
            prefs = dict(ctx.preferences or {})
            if profile.cooking_time_minutes is not None:
                prefs['cooking_time_minutes'] = profile.cooking_time_minutes
            if profile.meals_per_day is not None:
                prefs['meals_per_day'] = profile.meals_per_day
            if profile.activity_level:
                prefs['activity_level'] = profile.activity_level
            if profile.training_days_per_week is not None:
                prefs['training_days_per_week'] = profile.training_days_per_week
            if profile.training_level:
                prefs['training_level'] = profile.training_level
            if profile.training_time:
                prefs['training_time_of_day'] = profile.training_time
            if profile.hunger_pattern:
                prefs['hunger_pattern'] = profile.hunger_pattern
            ctx.preferences = prefs or None

        if policy is not None:
            if ctx.wake_time is None:
                ctx.wake_time = policy.wake_time
            if ctx.sleep_time is None:
                ctx.sleep_time = policy.sleep_time
            if ctx.preferred_training_time is None:
                ctx.preferred_training_time = policy.training_hour
            ctx.timezone = policy.timezone or ctx.timezone or DEFAULT_TIMEZONE
            if policy.work_start or policy.work_end or policy.work_pattern:
                ctx.working_hours = {
                    'pattern': policy.work_pattern,
                    'start': policy.work_start.isoformat() if policy.work_start else None,
                    'end': policy.work_end.isoformat() if policy.work_end else None,
                }

        if ctx.timezone is None:
            ctx.timezone = DEFAULT_TIMEZONE
        if ctx.wake_time is None:
            ctx.wake_time = DEFAULT_WAKE
        if ctx.sleep_time is None:
            ctx.sleep_time = DEFAULT_SLEEP


context_service = ContextService()
