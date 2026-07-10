from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.meal import MealCreate as MealCreateSchema
from app.schemas.meal import MealUpdate as MealUpdateSchema
from app.schemas.meal import ErrorResponse
from app.models.meal import Meal as MealModel
from app.database.database import get_db
from app.schemas.meal import MealResponse as MealResponseSchema

router = APIRouter()

MEAL_NOT_FOUND_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Meal not found',
        'model': ErrorResponse,
    },
}


@router.post('/', response_model=MealResponseSchema, status_code=status.HTTP_201_CREATED)
def create_meal(meal: MealCreateSchema, db: Session = Depends(get_db)):
    meal_db = MealModel(**meal.model_dump())
    db.add(meal_db)
    db.commit()
    db.refresh(meal_db)
    return meal_db


@router.put(
    '/{meal_id}',
    response_model=MealResponseSchema,
    responses=MEAL_NOT_FOUND_RESPONSES,
)
def update_meal(meal_id: int, meal: MealUpdateSchema, db: Session = Depends(get_db)):
    meal_db = db.query(MealModel).filter(MealModel.id == meal_id).first()
    if not meal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal not found')
    for field, value in meal.model_dump(exclude_unset=True).items():
        setattr(meal_db, field, value)
    db.commit()
    db.refresh(meal_db)
    return meal_db


@router.delete(
    '/{meal_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=MEAL_NOT_FOUND_RESPONSES,
)
def delete_meal(meal_id: int, db: Session = Depends(get_db)):
    meal_db = db.query(MealModel).filter(MealModel.id == meal_id).first()
    if not meal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal not found')
    db.delete(meal_db)
    db.commit()


@router.get('/', response_model=list[MealResponseSchema])
def get_meals(db: Session = Depends(get_db)):
    meals_db = db.query(MealModel).all()
    return meals_db


@router.get(
    '/{meal_id}',
    response_model=MealResponseSchema,
    responses=MEAL_NOT_FOUND_RESPONSES,
)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    meal_db = db.query(MealModel).filter(MealModel.id == meal_id).first()
    if not meal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal not found')
    return meal_db
