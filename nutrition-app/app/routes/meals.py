from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.meal import Meal, MealCreate
from app.models.meal import Meal as MealModel
from app.database.database import get_db


router = APIRouter()

@router.post('/', response_model=Meal)
def create_meal(meal: MealCreate, db: Session = Depends(get_db)):
    meal_db = MealModel(**meal.model_dump())

    db.add(meal_db)
    db.commit()
    db.refresh(meal_db)
    return meal_db

@router.get('/', response_model=list[Meal])
def get_meals(db: Session = Depends(get_db)):
    meals_db = db.query(MealModel).all()
    return meals_db

@router.get('/{meal_id}', response_model=Meal)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    meal_db = db.query(MealModel).filter(MealModel.id == meal_id).first()
    return meal_db

