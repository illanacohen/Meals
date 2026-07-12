"""App settings from environment variables."""

from __future__ import annotations

import os


def get_database_url() -> str:
    """Resolve DB URL. Local default: SQLite file. Cloud: set DATABASE_URL (Postgres)."""
    return os.getenv('DATABASE_URL', 'sqlite:///life_planner.db')


def get_cors_origins() -> list[str]:
    """Comma-separated origins, e.g. https://app.example.com,http://localhost:3000.

    Empty / unset → CORS middleware not needed (API-only /docs).
    Use * to allow all (demo only).
    """
    raw = os.getenv('CORS_ORIGINS', '').strip()
    if not raw:
        return []
    if raw == '*':
        return ['*']
    return [origin.strip() for origin in raw.split(',') if origin.strip()]


def run_migrations_on_startup() -> bool:
    return os.getenv('RUN_MIGRATIONS_ON_STARTUP', '').lower() in ('1', 'true', 'yes')
