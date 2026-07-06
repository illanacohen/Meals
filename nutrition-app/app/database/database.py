from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


DATABASE_URL = 'sqlite:///nutrition.db'

engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False}
)

session_local = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)


def get_db():
    db = session_local()
    try:
        yield db
    except:
        db.close()