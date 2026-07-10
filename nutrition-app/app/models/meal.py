from sqlalchemy import Column, Integer, String, Float
from app.database.base import Base


class Meal(Base):
    __tablename__ = 'meals'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
