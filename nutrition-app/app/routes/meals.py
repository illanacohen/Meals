from fastapi import APIRouter

router = APIRouter()

fake_db = []


@router.post('/')
def create_meal(meal: dict):
    fake_db.append(meal)
    return meal

@router.get('/')
def get_meals():
    return fake_db

@router.get('/{meal_id}')
def get_meal(meal_id: int):
    return
