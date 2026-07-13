from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.plan import Habit, Pillar, Plan, ProgressEntry, TodayTask
from app.models.user_profile import UserProfile
from app.repositories import pillar as pillar_repo
from app.schemas.meal import ErrorResponse
from app.schemas.plan import (
    DailyPlannerResponse,
    DailyTaskResponse,
    DailyTaskToggle,
    DayBlockResponse,
    HabitCreate,
    HabitResponse,
    PillarCreate,
    PillarResponse,
    PillarUpdate,
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    ProgressCreate,
    ProgressResponse,
)
from app.repositories import execution as execution_repo
from app.schemas.execution import (
    DynamicExecutionItemCreate,
    DynamicExecutionItemResponse,
    DynamicExecutionItemUpdate,
    ExecutionItemCreate,
    ExecutionItemResponse,
    ExecutionItemUpdate,
    PlanProposalCreate,
    PlanProposalResponse,
    PlanProposalUpdate,
)
from app.services.execution import build_today, registered_modules, toggle_today_task
from app.services.execution.seeding import ensure_habit_execution_item, seed_plan_hygiene_execution_items
from app.services.pillars.seeding import get_pillar_for_plan

router = APIRouter()

NOT_FOUND = {status.HTTP_404_NOT_FOUND: {'model': ErrorResponse}}


def _get_plan_or_404(plan_id: int, db: Session) -> Plan:
    plan = (
        db.query(Plan)
        .options(joinedload(Plan.habits), joinedload(Plan.pillars))
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
    """Create a Plan and seed long-lived hygiene ExecutionItems (pillars are user-defined)."""
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
    seed_plan_hygiene_execution_items(db, plan)
    db.commit()
    return _get_plan_or_404(plan.id, db)


@router.get('/', response_model=list[PlanResponse])
def list_plans(
    status_filter: str | None = Query(default=None, alias='status'),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Plan)
        .options(joinedload(Plan.habits), joinedload(Plan.pillars))
        .order_by(Plan.start_date.desc())
    )
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


@router.get('/{plan_id}/pillars', response_model=list[PillarResponse], responses=NOT_FOUND)
def list_plan_pillars(
    plan_id: int,
    enabled_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    return pillar_repo.list_pillars(db, plan_id, enabled_only=enabled_only)


@router.post(
    '/{plan_id}/pillars',
    response_model=PillarResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_plan_pillar(plan_id: int, payload: PillarCreate, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    existing = (
        db.query(Pillar)
        .filter(Pillar.plan_id == plan_id, Pillar.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Pillar name already exists')
    pillar = pillar_repo.create_pillar(db, plan_id, **payload.model_dump())
    db.commit()
    db.refresh(pillar)
    return pillar


@router.patch(
    '/{plan_id}/pillars/{pillar_id}',
    response_model=PillarResponse,
    responses=NOT_FOUND,
)
def update_plan_pillar(
    plan_id: int,
    pillar_id: int,
    payload: PillarUpdate,
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    pillar = pillar_repo.get_pillar(db, plan_id, pillar_id)
    if not pillar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Pillar not found')
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(pillar, key, value)
    db.commit()
    db.refresh(pillar)
    return pillar


@router.delete(
    '/{plan_id}/pillars/{pillar_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_plan_pillar(plan_id: int, pillar_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    pillar = pillar_repo.get_pillar(db, plan_id, pillar_id)
    if not pillar:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Pillar not found')
    db.delete(pillar)
    db.commit()


@router.post(
    '/{plan_id}/habits',
    response_model=HabitResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def add_habit(plan_id: int, payload: HabitCreate, db: Session = Depends(get_db)):
    plan = _get_plan_or_404(plan_id, db)
    data = payload.model_dump()
    pillar_id = data.pop('pillar_id', None)
    resolved_pillar_id = None
    if pillar_id is not None:
        try:
            resolved_pillar_id = get_pillar_for_plan(db, plan, pillar_id).id
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    habit = Habit(plan_id=plan_id, pillar_id=resolved_pillar_id, **data)
    db.add(habit)
    db.flush()
    ensure_habit_execution_item(db, plan, habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get(
    '/{plan_id}/execution-items',
    response_model=list[ExecutionItemResponse],
    responses=NOT_FOUND,
)
def list_execution_items(
    plan_id: int,
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    items = execution_repo.list_execution_items(db, plan_id, active_only=active_only)
    return [ExecutionItemResponse.from_orm_item(i) for i in items]


@router.post(
    '/{plan_id}/execution-items',
    response_model=ExecutionItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_execution_item(
    plan_id: int,
    payload: ExecutionItemCreate,
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.create_execution_item(db, plan_id, **payload.model_dump())
    db.commit()
    db.refresh(item)
    return ExecutionItemResponse.from_orm_item(item)


@router.patch(
    '/{plan_id}/execution-items/{item_id}',
    response_model=ExecutionItemResponse,
    responses=NOT_FOUND,
)
def update_execution_item(
    plan_id: int,
    item_id: int,
    payload: ExecutionItemUpdate,
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.get_execution_item(db, plan_id, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ExecutionItem not found')
    data = payload.model_dump(exclude_unset=True)
    if 'metadata' in data:
        item.item_metadata = data.pop('metadata')
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return ExecutionItemResponse.from_orm_item(item)


@router.delete(
    '/{plan_id}/execution-items/{item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_execution_item(plan_id: int, item_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.get_execution_item(db, plan_id, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='ExecutionItem not found')
    db.delete(item)
    db.commit()


@router.get(
    '/{plan_id}/dynamic-items',
    response_model=list[DynamicExecutionItemResponse],
    responses=NOT_FOUND,
)
def list_dynamic_items(plan_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    return execution_repo.list_dynamic_items(db, plan_id)


@router.post(
    '/{plan_id}/dynamic-items',
    response_model=DynamicExecutionItemResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_dynamic_item(
    plan_id: int,
    payload: DynamicExecutionItemCreate,
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.create_dynamic_item(db, plan_id, **payload.model_dump())
    db.commit()
    db.refresh(item)
    return item


@router.patch(
    '/{plan_id}/dynamic-items/{item_id}',
    response_model=DynamicExecutionItemResponse,
    responses=NOT_FOUND,
)
def update_dynamic_item(
    plan_id: int,
    item_id: int,
    payload: DynamicExecutionItemUpdate,
    db: Session = Depends(get_db),
):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.get_dynamic_item(db, plan_id, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='DynamicExecutionItem not found')
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete(
    '/{plan_id}/dynamic-items/{item_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND,
)
def delete_dynamic_item(plan_id: int, item_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    item = execution_repo.get_dynamic_item(db, plan_id, item_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='DynamicExecutionItem not found')
    db.delete(item)
    db.commit()


@router.get(
    '/{plan_id}/proposals',
    response_model=list[PlanProposalResponse],
    responses=NOT_FOUND,
)
def list_plan_proposals(plan_id: int, db: Session = Depends(get_db)):
    _get_plan_or_404(plan_id, db)
    return execution_repo.list_proposals(db, plan_id)


@router.post(
    '/{plan_id}/proposals',
    response_model=PlanProposalResponse,
    status_code=status.HTTP_201_CREATED,
    responses=NOT_FOUND,
)
def create_plan_proposal(
    plan_id: int,
    payload: PlanProposalCreate,
    db: Session = Depends(get_db),
):
    """Create a PlanProposal — never mutates the Plan automatically."""
    _get_plan_or_404(plan_id, db)
    proposal = execution_repo.create_proposal(db, plan_id, **payload.model_dump())
    db.commit()
    db.refresh(proposal)
    return proposal


@router.patch(
    '/{plan_id}/proposals/{proposal_id}',
    response_model=PlanProposalResponse,
    responses=NOT_FOUND,
)
def update_plan_proposal(
    plan_id: int,
    proposal_id: int,
    payload: PlanProposalUpdate,
    db: Session = Depends(get_db),
):
    """Accept or reject a proposal. Acceptance does not auto-apply changes yet."""
    _get_plan_or_404(plan_id, db)
    proposal = execution_repo.get_proposal(db, plan_id, proposal_id)
    if not proposal:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='PlanProposal not found')
    if payload.status not in ('pending', 'accepted', 'rejected'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid status')
    proposal.status = payload.status
    db.commit()
    db.refresh(proposal)
    return proposal


@router.get('/{plan_id}/today', response_model=DailyPlannerResponse, responses=NOT_FOUND)
def get_today_planner(
    plan_id: int,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """TODAY — Execution Engine home surface."""
    plan = _get_plan_or_404(plan_id, db)
    target = day or date.today()
    blocks, tasks = build_today(db, plan, target)
    return _today_response(plan, target, blocks, tasks)


@router.get('/{plan_id}/execution/today', response_model=DailyPlannerResponse, responses=NOT_FOUND)
def get_execution_today(
    plan_id: int,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Explicit Execution Engine entrypoint (same payload as /today)."""
    return get_today_planner(plan_id=plan_id, day=day, db=db)


@router.get('/{plan_id}/execution/modules')
def get_execution_modules(plan_id: int, db: Session = Depends(get_db)):
    """List modules registered with the Execution Engine."""
    _get_plan_or_404(plan_id, db)
    return {'modules': registered_modules()}


@router.patch(
    '/{plan_id}/today/{task_id}',
    response_model=DailyPlannerResponse,
    responses=NOT_FOUND,
)
def toggle_today_task_route(
    plan_id: int,
    task_id: int,
    payload: DailyTaskToggle,
    day: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    plan = _get_plan_or_404(plan_id, db)
    target = day or date.today()
    task = (
        db.query(TodayTask)
        .filter(TodayTask.id == task_id, TodayTask.plan_id == plan_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Task not found')
    blocks, tasks = toggle_today_task(db, plan, task, payload.completed, target)
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
