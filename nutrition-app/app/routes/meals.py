from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.schemas.meal import MealCreate as MealCreateSchema
from app.schemas.meal import MealUpdate as MealUpdateSchema
from app.schemas.meal import ErrorResponse
from app.models.meal import Meal as MealModel
from app.models.meal import MealItem as MealItemModel
from app.database.database import get_db
from app.schemas.meal import MealResponse as MealResponseSchema

router = APIRouter()

MEAL_NOT_FOUND_RESPONSES = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Meal not found',
        'model': ErrorResponse,
    },
}


def _get_meal_or_404(meal_id: int, db: Session) -> MealModel:
    meal_db = (
        db.query(MealModel)
        .options(joinedload(MealModel.items))
        .filter(MealModel.id == meal_id)
        .first()
    )
    if not meal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal not found')
    return meal_db


@router.post('/', response_model=MealResponseSchema, status_code=status.HTTP_201_CREATED)
def create_meal(meal: MealCreateSchema, db: Session = Depends(get_db)):
    meal_data = meal.model_dump(exclude={'items'})
    meal_db = MealModel(**meal_data)
    meal_db.items = [
        MealItemModel(name=item.name, grams=item.grams)
        for item in meal.items
    ]
    db.add(meal_db)
    db.commit()
    return _get_meal_or_404(meal_db.id, db)


@router.put(
    '/{meal_id}',
    response_model=MealResponseSchema,
    responses=MEAL_NOT_FOUND_RESPONSES,
)
def update_meal(meal_id: int, meal: MealUpdateSchema, db: Session = Depends(get_db)):
    meal_db = _get_meal_or_404(meal_id, db)
    update_data = meal.model_dump(exclude_unset=True, exclude={'items'})
    for field, value in update_data.items():
        setattr(meal_db, field, value)

    if meal.items is not None:
        meal_db.items.clear()
        meal_db.items = [
            MealItemModel(name=item.name, grams=item.grams)
            for item in meal.items
        ]

    db.commit()
    return _get_meal_or_404(meal_id, db)


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
    return db.query(MealModel).options(joinedload(MealModel.items)).all()


@router.get(
    '/{meal_id}',
    response_model=MealResponseSchema,
    responses=MEAL_NOT_FOUND_RESPONSES,
)
def get_meal(meal_id: int, db: Session = Depends(get_db)):
    return _get_meal_or_404(meal_id, db)
