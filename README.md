# Life Planner

### AI-Powered Life Execution System

<!-- When the web MVP exists, place logo + screenshot here (above the fold). -->

Life Planner transforms long-term goals into structured daily execution.

Instead of managing nutrition, workouts, and habits separately, everything converges into a single adaptive execution plan centered around **TODAY**.

> **Plan → Execute → Adapt.**

```text
                 GOAL
                   │
                   ▼
                 PLAN
                   │
                   ▼
                 TODAY
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Nutrition    Workout     Habits
        │          │          │
        └──────────┼──────────┘
                   ▼
               PROGRESS
                   │
                   ▼
                 PLAN
```

*AI-assisted planning and adaptation are part of the roadmap.*

---

## The Problem

Most people don't fail because they lack information.

They fail because every day they have to renegotiate hundreds of small decisions:

- What should I eat?
- Should I train today?
- When should I work?
- Can I skip this habit?
- What should I do next?

Life Planner reduces that cognitive load by turning long-term goals into a clear daily execution system—**TODAY**.

---

## The Solution

Life Planner goes beyond calorie tracking and workout logging by turning them into components of a unified execution plan.

The hardest part of improving your health isn't knowing what to do—it's consistently executing the right actions every day. Life Planner reduces decision fatigue by turning long-term goals into a clear daily execution plan.

The long-term north star is simple:

**Choose a goal → receive a complete Plan → run TODAY → let the system propose adjustments.**

The product is about **execution**. Fitness is the first domain; pillars like money or study join the same Plan → TODAY loop only when they are designed to belong there.

A useful filter for new features: *Does this help the user execute today's plan and stay aligned with their goal?* If not, it probably does not belong in Life Planner.

---

## Core pillars

Life Planner treats wellbeing as multidimensional. Fitness is the first domain; new pillars join only when they fit the domain model and feed **TODAY**.

In scope today (shipped or designed):

- **Nutrition**
- **Training**
- **Habits**
- **Recovery & Sleep**
- **Financial Wellness**
- **Daily Planning (TODAY)**

Each pillar contributes to the same execution plan instead of existing as an isolated tracker.

---

## Features

| Capability | Description |
|------------|-------------|
| **Goal-based planning** | Define outcomes (fat loss, muscle gain, maintenance, performance, habit focus) and turn them into time-boxed Plans. |
| **Nutrition planning** | Macro targets, daily meal structure, recipes/library, and meal suggestions that fit remaining macros. |
| **Workout planning** | Training programs structured by weeks, days, exercises, sets, and progression (domain models in place; APIs expanding). |
| **Habit tracking** | Plan-scoped habits with completions—designed for linchpin behaviors and non-negotiable minimums. |
| **Daily planner (TODAY)** | The home surface: one checklist where every active pillar executes together. |
| **Progress tracking** | Weight, adherence, and objective entries that support weekly review. |
| **AI Coach** | Roadmap: generate and revise Plans via reviewable proposals—not a free-form chat that bypasses domain rules. |
| **Smart recommendations** | Meal suggestions from remaining macros; roadmap includes adaptation signals and proposal-based changes. |
| **Shopping lists** | Aggregate ingredients across planned days into a ready-to-shop list. |

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

### Planned — Product
- Full AI Coach (generate Plan + `PlanProposal` accept/reject flow)
- Adaptation engine (weekly rules → proposals)
- Check-ins (structured reflection vs raw metrics)
- Recovery & sleep as a first-class pillar
- Financial Wellness (budget wellbeing, enjoyment budget, goals)
- Exercise catalog, richer progression
- Calendar sync
- Frontend clients and mobile UX

### Planned — Platform
- Authentication and multi-user tenancy
- Notifications
- Cloud object storage (e.g. S3)
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

**Life Planner** — Plan → Execute → Adapt. Everything runs through TODAY.
