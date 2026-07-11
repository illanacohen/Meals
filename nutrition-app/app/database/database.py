from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_database_url

DATABASE_URL = get_database_url()

_connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    _connect_args = {'check_same_thread': False}

engine = create_engine(DATABASE_URL, connect_args=_connect_args)

session_local = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine,
)


def get_db():
    db = session_local()
    try:
        yield db
    finally:
        db.close()
