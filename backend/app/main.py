from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_cors_origins, run_migrations_on_startup


def _maybe_upgrade_db() -> None:
    if not run_migrations_on_startup():
        return
    from alembic import command
    from alembic.config import Config

    alembic_cfg = Config('alembic.ini')
    command.upgrade(alembic_cfg, 'head')


@asynccontextmanager
async def lifespan(_app: FastAPI):
    _maybe_upgrade_db()
    yield


app = FastAPI(lifespan=lifespan)

origins = get_cors_origins()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app.include_router(api_router)


@app.get('/')
def sanity_check():
    return {'status': 'ok'}
