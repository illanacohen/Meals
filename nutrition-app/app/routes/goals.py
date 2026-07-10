from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.models.meal import DailyGoal as DailyGoalModel
from app.schemas.meal import DailyGoalCreate
from app.schemas.meal import DailyGoalResponse
from app.schemas.meal import DailyGoalUpdate
from app.schemas.meal import ErrorResponse

router = APIRouter()

NOT_FOUND = {
    status.HTTP_404_NOT_FOUND: {
        'description': 'Daily goal not found',
        'model': ErrorResponse,
    },
}


@router.post('/', response_model=DailyGoalResponse, status_code=status.HTTP_201_CREATED)
def create_daily_goal(goal: DailyGoalCreate, db: Session = Depends(get_db)):
    existing = db.query(DailyGoalModel).filter(DailyGoalModel.date == goal.date).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f'Daily goal already exists for {goal.date}',
        )

    goal_db = DailyGoalModel(**goal.model_dump())
    db.add(goal_db)
    db.commit()
    db.refresh(goal_db)
    return goal_db


@router.get('/', response_model=list[DailyGoalResponse])
def list_daily_goals(db: Session = Depends(get_db)):
    return db.query(DailyGoalModel).order_by(DailyGoalModel.date.desc()).all()


@router.get('/by-date/{goal_date}', response_model=DailyGoalResponse, responses=NOT_FOUND)
def get_daily_goal_by_date(goal_date: date, db: Session = Depends(get_db)):
    goal = db.query(DailyGoalModel).filter(DailyGoalModel.date == goal_date).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Daily goal not found')
    return goal


@router.get('/{goal_id}', response_model=DailyGoalResponse, responses=NOT_FOUND)
def get_daily_goal(goal_id: int, db: Session = Depends(get_db)):
    goal = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Daily goal not found')
    return goal


@router.put('/{goal_id}', response_model=DailyGoalResponse, responses=NOT_FOUND)
def update_daily_goal(goal_id: int, goal: DailyGoalUpdate, db: Session = Depends(get_db)):
    goal_db = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).first()
    if not goal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Daily goal not found')

    for field, value in goal.model_dump(exclude_unset=True).items():
        setattr(goal_db, field, value)

    db.commit()
    db.refresh(goal_db)
    return goal_db


@router.delete('/{goal_id}', status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_daily_goal(goal_id: int, db: Session = Depends(get_db)):
    goal_db = db.query(DailyGoalModel).filter(DailyGoalModel.id == goal_id).first()
    if not goal_db:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Daily goal not found')
    db.delete(goal_db)
    db.commit()
