import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app

# Ensure all models are registered on Base.metadata
from app.models.meal import (  # noqa: F401
    DailyGoal,
    Meal,
    MealItem,
    MealPlan,
    MealSlot,
    MealTemplate,
    MealTemplateItem,
)
from app.models.user_profile import UserProfile  # noqa: F401
from app.models.context import UserContext  # noqa: F401
from app.models.plan import (  # noqa: F401
    DailyTask,
    Habit,
    HabitCompletion,
    Pillar,
    Plan,
    ProgressEntry,
    TodayTask,
    WorkoutDay,
    WorkoutExercise,
    WorkoutProgram,
)
from app.models.planner import (  # noqa: F401
    DayBlock,
    DaySchedulePolicy,
    PlanTask,
    TaskTemplate,
)
from app.models.execution import (  # noqa: F401
    DynamicExecutionItem,
    ExecutionCompletion,
    ExecutionItem,
    PlanProposal,
)


@pytest.fixture()
def db_session():
    engine = create_engine(
        'sqlite://',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
