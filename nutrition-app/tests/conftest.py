import json
import time
import warnings

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.database import get_db
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

_LOG_PATH = r'c:\Users\felic\OneDrive\Desktop\Work\Meals\debug-d5b7d2.log'


def _dbg(hypothesis_id, location, message, data=None, run_id='pre-fix'):
    # #region agent log
    with open(_LOG_PATH, 'a', encoding='utf-8') as _f:
        _f.write(json.dumps({
            'sessionId': 'd5b7d2',
            'runId': run_id,
            'hypothesisId': hypothesis_id,
            'location': location,
            'message': message,
            'data': data or {},
            'timestamp': int(time.time() * 1000),
        }, ensure_ascii=False) + '\n')
    # #endregion


@pytest.fixture(scope='session', autouse=True)
def _log_http_client_backend():
    httpx2_ok = False
    try:
        import httpx2  # noqa: F401
        httpx2_ok = True
    except ModuleNotFoundError:
        httpx2_ok = False
    _dbg('H1', 'conftest.py:session', 'httpx2 import check', {'httpx2_installed': httpx2_ok}, run_id='post-fix')
    yield


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
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        with TestClient(app) as test_client:
            deprecations = [
                str(w.message)
                for w in caught
                if 'httpx' in str(w.message).lower() or 'httpx2' in str(w.message).lower()
            ]
            _dbg('H2', 'conftest.py:client', 'TestClient warning capture', {
                'httpx_deprecation_warnings': deprecations,
                'warning_count': len(deprecations),
            }, run_id='post-fix')
            yield test_client
    app.dependency_overrides.clear()
