from sqlalchemy import Column, Integer, String, Float, Date
from db import Base


class Meal(Base):
    __tablename__ = 'meals'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
