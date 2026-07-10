from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.database.database import get_db
from app.models.meal import Meal as MealModel
from app.models.meal import MealTemplate as MealTemplateModel
from app.models.meal import MealTemplateItem as MealTemplateItemModel
from app.schemas.meal import ErrorResponse
from app.schemas.meal import MealTemplateCreate
from app.schemas.meal import MealTemplateResponse
from app.schemas.meal import MealTemplateUpdate
from app.services.food_catalog import FoodResolutionError, build_meal_item_fields

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Template not found',
        'model': ErrorResponse,
    },
}


def _get_template_or_404(template_id: int, db: Session) -> MealTemplateModel:
    template = (
        db.query(MealTemplateModel)
        .options(joinedload(MealTemplateModel.items))
        .filter(MealTemplateModel.id == template_id)
        .first()
    )
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal template not found')
    return template


def _build_template_items(items) -> list[MealTemplateItemModel]:
    try:
        return [MealTemplateItemModel(**build_meal_item_fields(item)) for item in items]
    except FoodResolutionError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post('/', response_model=MealTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(payload: MealTemplateCreate, db: Session = Depends(get_db)):
    existing = db.query(MealTemplateModel).filter(MealTemplateModel.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Template "{payload.name}" already exists',
        )

    template = MealTemplateModel(
        name=payload.name,
        calories=payload.calories,
        protein=payload.protein,
        fat=payload.fat,
        carbs=payload.carbs,
        fiber=payload.fiber,
        items=_build_template_items(payload.items),
    )
    db.add(template)
    db.commit()
    return _get_template_or_404(template.id, db)


@router.post(
    '/from-meal/{meal_id}',
    response_model=MealTemplateResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def save_meal_as_template(meal_id: int, name: str | None = None, db: Session = Depends(get_db)):
    """One-click: save an existing meal into the library."""
    meal = (
        db.query(MealModel)
        .options(joinedload(MealModel.items))
        .filter(MealModel.id == meal_id)
        .first()
    )
    if not meal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal not found')

    template_name = name or meal.name
    existing = db.query(MealTemplateModel).filter(MealTemplateModel.name == template_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Template "{template_name}" already exists',
        )

    template = MealTemplateModel(
        name=template_name,
        calories=meal.calories,
        protein=meal.protein,
        fat=meal.fat,
        carbs=meal.carbs,
        fiber=meal.fiber,
        items=[
            MealTemplateItemModel(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                grams=item.grams,
            )
            for item in meal.items
        ],
    )
    db.add(template)
    db.commit()
    return _get_template_or_404(template.id, db)


@router.get('/', response_model=list[MealTemplateResponse])
def list_templates(db: Session = Depends(get_db)):
    return (
        db.query(MealTemplateModel)
        .options(joinedload(MealTemplateModel.items))
        .order_by(MealTemplateModel.name.asc())
        .all()
    )


@router.get('/{template_id}', response_model=MealTemplateResponse, responses=NOT_FOUND)
def get_template(template_id: int, db: Session = Depends(get_db)):
    return _get_template_or_404(template_id, db)


@router.put('/{template_id}', response_model=MealTemplateResponse, responses=NOT_FOUND)
def update_template(
    template_id: int,
    payload: MealTemplateUpdate,
    db: Session = Depends(get_db),
):
    template = _get_template_or_404(template_id, db)
    data = payload.model_dump(exclude_unset=True, exclude={'items'})

    if 'name' in data:
        clash = (
            db.query(MealTemplateModel)
            .filter(MealTemplateModel.name == data['name'], MealTemplateModel.id != template_id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f'Template "{data["name"]}" already exists',
            )

    for field, value in data.items():
        setattr(template, field, value)

    if payload.items is not None:
        template.items.clear()
        template.items = _build_template_items(payload.items)

    db.commit()
    return _get_template_or_404(template_id, db)


@router.delete('/{template_id}', status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    template = db.query(MealTemplateModel).filter(MealTemplateModel.id == template_id).first()
    if not template:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meal template not found')
    db.delete(template)
    db.commit()
