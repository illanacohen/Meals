from pydantic import PostgresDsn
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = 'postgresql://user:pass@db:5432/nutrition'

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)

base = declarative_base()
