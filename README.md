# Life Planner

### AI-Powered Health & Performance Planner

Life Planner helps people **reach health and performance goals** through intelligent planning—not endless logging.

Most tools ask you to record what you already did. Life Planner starts from the opposite direction: you define an objective, the system builds an executable **Plan** (nutrition, training, habits), and you run your day from a single checklist. Progress and context then feed smart adjustments—so the plan stays aligned with real life.

> **Plan → Execute → Adapt.**  
> Nutrition, training, and habits are modules of one strategy—not separate apps.

---

## Features

| Capability | Description |
|------------|-------------|
| **Goal-based planning** | Define outcomes (fat loss, muscle gain, maintenance, performance, habit focus) and turn them into time-boxed Plans. |
| **Nutrition planning** | Macro targets, daily meal structure, recipes/library, and meal suggestions that fit remaining macros. |
| **Workout planning** | Training programs structured by weeks, days, exercises, sets, and progression (domain models in place; APIs expanding). |
| **Habit tracking** | Plan-scoped habits with completions—designed for linchpin behaviors and non-negotiable minimums. |
| **Daily planner** | A unified **TODAY** checklist so execution is one place, not three apps. |
| **Progress tracking** | Weight, adherence, and objective entries that support weekly review. |
| **AI Coach** | Designed to generate and revise Plans via reviewable proposals—not a free-form chat that bypasses domain rules. |
| **Smart recommendations** | Meal suggestions from remaining macros; roadmap includes adaptation signals and proposal-based changes. |
| **Shopping lists** | Aggregate ingredients across planned days into a ready-to-shop list. |
| **Future integrations** | Auth, multi-user, cloud object storage, CI/CD, and richer coach workflows. |

---

## Product vision

Life Planner is not a calorie counter or a workout logger.

It is a **personal operating system for health and performance**: an intelligent layer that helps users **plan** a strategy, **execute** it day by day, and **adapt** when circumstances change—so willpower and constant renegotiation stop being the bottleneck.

The long-term north star is simple:

**Choose a goal → receive a complete Plan → run TODAY → let the system propose adjustments.**

---

## Architecture

The backend follows **lightweight domain-driven design**: high cohesion inside modules, low coupling between them, with **Plan** as the aggregate root of execution.

```text
backend/
├── app/
│   ├── api/                 # HTTP router
│   ├── core/                # Config (DATABASE_URL, CORS, …)
│   ├── db/                  # SQLAlchemy Base & session
│   ├── models/              # Domain persistence
│   ├── schemas/             # Pydantic contracts
│   ├── repositories/        # Aggregate data access
│   ├── services/
│   │   ├── planner/         # Plan lifecycle & daily checklist
│   │   ├── nutrition/       # Macros, catalog, suggest, shopping
│   │   ├── workouts/        # Training programs
│   │   ├── habits/          # Habit definitions & completions
│   │   ├── progress/        # Measurements & adherence
│   │   └── ai/              # Coach / Plan proposals
│   ├── integrations/        # External providers (LLM, email, …)
│   ├── utils/
│   └── routes/              # Endpoint handlers by surface
├── alembic/                 # Migrations
├── docs/domain/             # Canonical domain model
├── tests/
├── Dockerfile
└── docker-compose.yml
```

Domain reference:

- [Domain model](backend/docs/domain/DOMAIN.md)
- [Gap analysis](backend/docs/domain/GAP_ANALYSIS.md)
- [Migration plan](backend/docs/domain/MIGRATION_PLAN.md)

**Layering:** Models hold structure and simple invariants; repositories load aggregates; **services** own use cases (activate a plan, rebuild TODAY, accept a proposal). Routes stay thin.

---

## Tech stack

| Technology | Role |
|------------|------|
| **Python 3.11+** | Language |
| **FastAPI** | HTTP API |
| **Pydantic** | Request/response validation |
| **SQLAlchemy** | ORM |
| **Alembic** | Schema migrations |
| **SQLite** | Local development default |
| **PostgreSQL** | Production / Docker Compose |
| **Uvicorn** | ASGI server |
| **Docker** | Containerized API + Postgres |
| **AWS** | Deployment roadmap (see below) |

---

## Roadmap

### Implemented
- Plan CRUD (goal type, duration, status)
- Habits on a Plan + daily checklist (`/plans/{id}/today`)
- Progress entries (weight, adherence)
- Nutrition module: meals, daily slots, macro goals, recipe library, meal suggest, shopping list aggregation
- Profile onboarding with BMR/TDEE and macro distribution
- Workout domain models (program → days → exercises)
- Config for `DATABASE_URL`, CORS, optional migrate-on-startup
- Docker Compose (API + Postgres)

### In progress
- Domain alignment (Goal entity, NutritionPlan, unified TODAY across meals + workouts)
- Workout services and APIs on top of existing models
- Stronger Plan ↔ nutrition day binding

### Planned
- Full AI Coach (generate Plan + `PlanProposal` accept/reject flow)
- Adaptation engine (weekly rules → proposals)
- Check-ins (structured reflection vs raw metrics)
- Auth and multi-user tenancy
- Exercise catalog, richer progression
- Frontend clients and mobile UX
- CI/CD and production AWS topology

---

## Getting started

### Prerequisites

- Python 3.11+
- pip
- Optional: Docker Desktop (for Postgres stack)

### Local (SQLite)

```bash
cd backend

python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
# source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head

python -m uvicorn app.main:app --reload
```

API: [http://127.0.0.1:8000](http://127.0.0.1:8000)  
Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Docker (PostgreSQL + API)

```bash
cd backend
docker compose up --build
```

Migrations run in the container entrypoint. Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

> Stop any local Uvicorn on port `8000` before Compose, or you may hit the wrong process.

### Environment

Copy [`backend/.env.example`](backend/.env.example):

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///life_planner.db` | Use `postgresql+psycopg://…` for Postgres |
| `CORS_ORIGINS` | _(empty)_ | Comma-separated origins, or `*` for demos |
| `RUN_MIGRATIONS_ON_STARTUP` | off | Set `true` when the process should run Alembic on boot |

### Tests

```bash
cd backend
python -m pytest -q
```

---

## Target cloud architecture

Intended production shape (roadmap—not all wired yet):

```text
GitHub  →  GitHub Actions (CI/CD)
                ↓
           Docker image
                ↓
        AWS EC2 / App Runner / ECS
                ↓
        ┌───────┴────────┐
        ▼                ▼
   Amazon RDS         Amazon S3
   (PostgreSQL)    (assets / exports)
```

| Component | Purpose |
|-----------|---------|
| **GitHub** | Source of truth |
| **GitHub Actions** | Test, build, deploy |
| **Docker** | Reproducible runtime |
| **EC2 / App Runner / ECS** | API hosting |
| **RDS** | Managed PostgreSQL |
| **S3** | Media, exports, backups of generated artifacts |

Local and Compose already use the same app image pattern; cloud deploy is the next ops milestone.

---

## API surfaces (developer map)

| Area | Prefix | Notes |
|------|--------|--------|
| Plans | `/plans` | Aggregate root: habits, TODAY, progress |
| Nutrition days | `/meal-plans` | Daily meal structure under the nutrition module |
| Meals / library / suggest / shopping | `/meals`, `/library`, `/suggest`, `/shopping-list` | Nutrition toolkit |
| Macro targets | `/goals` | Daily macro targets (nutrition) |
| Onboarding | `/onboarding` | Profile + energy/macro baseline |

Explore the live contract at `/docs`.

---

## Contributing

Contributions that respect the domain model are welcome:

1. Read [`docs/domain/DOMAIN.md`](backend/docs/domain/DOMAIN.md).
2. Keep **Plan** as the execution root; don’t introduce competing “plan” nouns for meal days.
3. Put use cases in **services**, not fat route handlers.
4. Add or update tests with behavior changes.
5. Prefer reviewable **PlanProposal**-style changes for system/AI mutations when that layer lands.

---

## License

Proprietary / TBD — update this section when you publish a license.

---

**Life Planner** — plan the strategy, execute the day, adapt with intelligence.
