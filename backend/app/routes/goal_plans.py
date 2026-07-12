from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.plan import DailyTask, Habit, Plan, ProgressEntry
from app.models.user_profile import UserProfile
from app.schemas.meal import ErrorResponse
from app.schemas.plan import (
    DailyPlannerResponse,
    DailyTaskResponse,
    DailyTaskToggle,
    DayBlockResponse,
    HabitCreate,
    HabitResponse,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    ProgressCreate,
    ProgressResponse,
)
from app.services.planner.daily import get_today_view, toggle_task
from app.services.planner.seeding import ensure_habit_plan_task, seed_plan_hygiene_tasks

router = APIRouter()

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {'model': ErrorResponse}}


def _get_plan_or_404(plan_id: int, db: Session) -> Plan:
    plan = (
        db.query(Plan)
        .options(joinedload(Plan.habits))
        .filter(Plan.id == plan_id)
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Plan not found')
    return plan


def _today_response(plan: Plan, target: date, blocks, tasks) -> DailyPlannerResponse:
    by_block: dict[str, list] = {b.block_type: [] for b in blocks}
    for t in tasks:
        key = t.block_type or 'execution'
        by_block.setdefault(key, []).append(t)

    block_payload = [
        DayBlockResponse(
            type=b.block_type,
            starts_at=b.starts_at,
            ends_at=b.ends_at,
            tasks=[DailyTaskResponse.model_validate(t) for t in by_block.get(b.block_type, [])],
        )
        for b in blocks
    ]
    completed = sum(1 for t in tasks if t.completed)
    return DailyPlannerResponse(
        plan_id=plan.id,
        date=target,
        blocks=block_payload,
        tasks=[DailyTaskResponse.model_validate(t) for t in tasks],
        completed_count=completed,
        total_count=len(tasks),
    )


@router.post('/', response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_plan(payload: PlanCreate, db: Session = Depends(get_db)):
    """Crear un Plan maestro (objetivo + duración) y seed hygiene PlanTasks."""
    profile = db.query(UserProfile).order_by(UserProfile.id.asc()).first()
    plan = Plan(
        name=payload.name,
        goal_type=payload.goal_type.value,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        duration_weeks=payload.duration_weeks,
        status=payload.status.value,
        strategy_notes=payload.strategy_notes,
        user_profile_id=profile.id if profile else None,
    )
    db.add(plan)
    db.flush()
    seed_plan_hygiene_tasks(db, plan)
    db.commit()
    return _get_plan_or_404(plan.id, db)


@router.get('/', response_model=list[PlanResponse])
def list_plans(
    status_filter: str | None = Query(default=None, alias='status'),
    db: Session = Depends(get_db),
):
    query = db.query(Plan).options(joinedload(Plan.habits)).order_by(Plan.start_date.desc())
    if status_filter:
        query = query.filter(Plan.status == status_filter)
    return query.all()


@router.get('/{plan_id}', response_model=PlanResponse, responses=NOT_FOUND)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    return _get_plan_or_404(plan_id, db)


@router.patch('/{plan_id}', response_model=PlanResponse, responses=NOT_FOUND)
def update_plan(plan_id: int, payload: PlanUpdate, db: Session = Depends(get_db)):
    plan = _get_plan_or_404(plan_id, db)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        if hasattr(value, 'value'):
            value = value.value
        setattr(plan, key, value)
    db.commit()
    return _get_plan_or_404(plan_id, db)


@router.delete('/{plan_id}', status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Plan not found')
    db.delete(plan)
    db.commit()


@router.post(
    '/{plan_id}/habits',
    response_model=HabitResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def add_habit(plan_id: int, payload: HabitCreate, db: Session = Depends(get_db)):
    plan = _get_plan_or_404(plan_id, db)
    habit = Habit(plan_id=plan_id, **payload.model_dump())
    db.add(habit)
    db.flush()
    ensure_habit_plan_task(db, plan, habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get('/{plan_id}/today', response_model=DailyPlannerResponse, responses=NOT_FOUND)
def get_today_planner(
    plan_id: int,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """TODAY home surface: DayBlocks with tasks (hygiene + habits + meals + workouts)."""
    plan = _get_plan_or_404(plan_id, db)
    target = day or date.today()
    blocks, tasks = get_today_view(db, plan, target)
    return _today_response(plan, target, blocks, tasks)


@router.patch(
    '/{plan_id}/today/{task_id}',
    response_model=DailyPlannerResponse,
    responses=NOT_FOUND,
)
def toggle_today_task(
    plan_id: int,
    task_id: int,
    payload: DailyTaskToggle,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    plan = _get_plan_or_404(plan_id, db)
    target = day or date.today()
    task = (
        db.query(DailyTask)
        .filter(DailyTask.id == task_id, DailyTask.plan_id == plan_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    blocks, tasks = toggle_task(db, plan, task, payload.completed, target)
    return _today_response(plan, target, blocks, tasks)


@router.post(
    '/{plan_id}/progress',
    response_model=ProgressResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def add_progress(plan_id: int, payload: ProgressCreate, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    entry = ProgressEntry(plan_id=plan_id, **payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@router.get('/{plan_id}/progress', response_model=list[ProgressResponse], responses=NOT_FOUND)
def list_progress(plan_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    return (
        db.query(ProgressEntry)
        .filter(ProgressEntry.plan_id == plan_id)
        .order_by(ProgressEntry.date.desc())
        .all()
    )
