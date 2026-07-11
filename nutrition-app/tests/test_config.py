import os

from app.core.config import get_cors_origins, get_database_url, run_migrations_on_startup


def test_database_url_default(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    assert get_database_url() == 'sqlite:///nutrition.db'


def test_database_url_from_env(monkeypatch):
    monkeypatch.setenv(
        'DATABASE_URL',
        'postgresql+psycopg://user:pass@localhost:5432/nutrition',
    )
    assert 'postgresql+psycopg' in get_database_url()


def test_cors_origins_parsing(monkeypatch):
    monkeypatch.setenv('CORS_ORIGINS', 'http://localhost:3000, https://app.example.com')
    assert get_cors_origins() == ['http://localhost:3000', 'https://app.example.com']

    monkeypatch.setenv('CORS_ORIGINS', '*')
    assert get_cors_origins() == ['*']

    monkeypatch.delenv('CORS_ORIGINS', raising=False)
    assert get_cors_origins() == []


def test_run_migrations_flag(monkeypatch):
    monkeypatch.setenv('RUN_MIGRATIONS_ON_STARTUP', 'true')
    assert run_migrations_on_startup() is True
    monkeypatch.delenv('RUN_MIGRATIONS_ON_STARTUP', raising=False)
    assert run_migrations_on_startup() is False
