# Life Planner

### AI-Powered Life Execution System

<!-- When the web MVP exists, place logo + screenshot here (above the fold). -->

**Life Planner is not designed to tell people what to do. It helps them build enough clarity that executing their own decisions becomes easier than renegotiating them.**

**Minimize self-negotiation.** Everything converges into one adaptive plan centered around **TODAY**—so you spend energy living the day, not reopening it.

> **Plan → Execution Engine → TODAY → Adapt.**

```text
                 GOAL
                   │
                   ▼
                 PLAN
                   │
                   ▼
            EXECUTION ENGINE
              ▲            ▲
              │            │
        UserContext    Current Date
              │
              ▼
              TODAY
                │
                ▼
             Progress
                │
                ▼
          Plan Adaptation
```

*AI-assisted planning and adaptation are part of the roadmap.*

---

## The Problem

Every human tries to project a better version of themselves and plan how to get there—from the note that says “diet and gym start tomorrow,” to the brand-new planner bought on January 1st. People want to change. They want order.

They don’t fail because they lack discipline, motivation, or information. They fail where the mind breaks **by design**—three historical friction points:

### 1. Decision fatigue (activation friction)

The brain burns enormous energy deciding *what* to do. If at 7:00 PM on a Monday you still have to ask: “What should I cook? Do I have the ingredients? Which muscle group was today?”—friction spikes high enough that dinner becomes delivery and the couch wins.

### 2. Disconnect from the “future self”

Sunday-you is logical and perfect (“I’ll train six days straight”). Wednesday-you, rainy, 6:00 AM, is emotional and wants to sleep. Plans written by the future-self optimist collide with the present-self who has to live them.

### 3. All-or-nothing guilt

Miss one day and the mind often abandons the whole process—“I already ruined it.” Perfection becomes the enemy of consistency.

That renegotiation—hundreds of micro-decisions reopened every day—often costs more energy than doing the thing. Life Planner exists to reduce that friction—not to lecture, guilt, or track for tracking’s sake.

---

## The Solution

Life Planner is not an exotic idea. It is an **execution facilitator**: operational support for willpower. Human willpower is limited and unreliable; the software’s job is to **automate consistency**.

The operating loop:

**Goal → Plan → Execution Engine (Plan + UserContext + date) → TODAY → Progress → Plan Adaptation.**

That loop attacks the three failure modes directly:

| Friction | How Life Planner responds |
|----------|---------------------------|
| **Decision fatigue** | You don’t “assemble your day.” The Execution Engine already processed your **Plan** and **UserContext** (e.g. late workday, low energy) and returns a small set of actions: *don’t think—execute*. |
| **Future-self disconnect** | TODAY is generated for *this* date and *this* context—not for Sunday’s idealized week. The plan holds the decisions; the engine projects what is realistic now. |
| **All-or-nothing guilt** | Missing the gym is not a red X that ends the arc. The **FrictionEngine** turns exception logs into reviewable **PlanProposal**s (e.g. reschedule / shorten)—the user stays on course without perfection theater. Proposals are not auto-applied; they are visual choices. |

Domains (health, work, money, personal life) are not the product. They are *how* clarity shows up: structure that answers today’s micro-decisions in advance so you don’t have to reopen them.

**Naming note:** A life **Goal** (intention) is product language; today the executable unit is a **Plan** with `goal_type`. The HTTP prefix `/goals` is unrelated—it stores **daily nutrition macro targets**.

A useful filter for new features:

1. Does this **reduce friction**?
2. Does it help the user **execute today’s plan**?
3. Does it reinforce **discipline or self-awareness**?
4. Does it **reduce decision fatigue**?

If the answer is no, it probably does not belong in Life Planner.

Full product specification (philosophy, knowledge module, canvas editing, identity vs streaks, imperfect execution): [`backend/docs/product/PRODUCT_DIRECTION.md`](backend/docs/product/PRODUCT_DIRECTION.md).

---

## The app must not become the work

The number-one failure mode of productivity apps: **they become a job of their own.** If “organizing my life” means twenty minutes a day filling spreadsheets, scoring tasks, and arguing with an AI, the app joins the friction—it is no longer the solution.

Users do not open Life Planner to chat or renegotiate. They open it to **execute** or to **log a deviation**. Friction data should be an almost invisible side effect of daily use—not a second career in self-administration.

**Design principle: passive metrics + ultra-short active input.** Manage by exception. Freedom to log—never an obligation to perform for the software.

| Mode | Meaning |
|------|---------|
| **Plan assumed running** | If the user says nothing, the system assumes the basic routine is flowing. Silence means *life is on plan*. |
| **Interact only on friction or real change** | Open the app when something hurt, when a habit is costing too much, or when a deviation matters—*“I skipped reading today”* / *“I finished training at 11pm and wrecked my sleep.”* |
| **Passive metrics** | Completions, timing, and adherence emerge from light use (or from integrations later)—not from daily questionnaires. |
| **Ultra-short active input** | When input is needed, it is a tap or a one-line note—not a negotiation loop. |

The product succeeds when it is **operational support for willpower**, not another inbox of chores.

---

## Product principles

- **Decide once, execute many times** — TODAY is the surface; the plan holds the decisions.
- **Silence = on plan** — no daily theater of check-ins; speak up only for friction or intentional change.
- **Passive metrics, minimal active input** — never make organizing life a second job.
- **Edit the plan like a canvas** — replace via structural alternatives (`/alternatives` + `/replace`); canvas UI still planned, no chat renegotiation loop.
- **Experience before explanation** — small personal experiments first; insight after living them, not lectures up front.
- **One Daily Insight** — at most one idea per day (short read or clip). Never a content feed.
- **Measure decisions avoided** — progress is not only tasks checked; a future **Negotiation Count** surfaces how many decisions the plan already settled so you didn’t reopen them (product concept—not shipped).

---

## Core pillars

Life Planner organizes life into interconnected domains that support the same long-term objective.

Rather than tracking each area independently, every domain’s job is to **pre-answer today’s micro-decisions** for that area and feed a single execution plan centered around **TODAY**.

**Product pillars (not all shipped)** — target map for the product; only some have backend APIs today:

- **Health** *(nutrition shipped; training models-only; recovery/sleep planned)*
  - Nutrition
  - Training
  - Recovery & Sleep
- **Personal Development** *(habits shipped; learning / deep work planned)*
  - Habits
  - Learning
  - Deep Work
- **Financial Wellbeing** *(vision)*
  - Budget
  - Spending
  - Financial Goals
- **Life Management** *(TODAY / execution / pillars shipped)*
  - Daily Planning
  - Routines
  - Personal Projects

Each domain exists to answer one question:

**What should I do today to become the person I want to be?**

---

## Features

| Capability | Status | Description |
|------------|--------|-------------|
| **Plan + TODAY** | **Shipped** | Time-boxed Plans; Execution Engine projects Plan + UserContext + date → TODAY. |
| **UserContext** | **Shipped** | Canonical execution context (`GET/PATCH /context`)—engine input, not a second profile API for modules. |
| **Execution items & logs** | **Shipped** | Long-lived Plan actions; optional **ExecutionLog** by exception (silence = on plan). |
| **Visual Replace** | **Shipped (API)** | `GET …/alternatives` + `POST …/replace`—structural cards, not chat. Canvas UI still planned. |
| **FrictionEngine → PlanProposal** | **Shipped (v0)** | Pattern detection over exception logs creates reviewable proposals; status accept/reject exists; apply-on-accept still planned. |
| **Pillars (user-defined)** | **Shipped** | CRUD under `/plans/{id}/pillars`. |
| **Habits on a Plan** | **Shipped** | Plan-scoped habits + TODAY projection (streak/non-negotiable UX still thin). |
| **Nutrition toolkit** | **Shipped** | Meals, slots, daily macro `/goals`, library, suggest, shopping list. |
| **Progress entries** | **Shipped** | Weight / adherence notes on a Plan. |
| **Onboarding** | **Shipped** | Profile + BMR/TDEE; produces UserContext. |
| **Workout programs** | **Models only** | Program → days → exercises in DB; **no workout HTTP API yet**. |
| **Life Goal entity** | **Vision** | Intention aggregate not implemented; Plans carry `goal_type` today. |
| **AI Coach (LLM)** | **Vision** | Infrastructure for proposals exists; LLM plan generation / coaching not shipped. |
| **Finance / Sleep / Learning** | **Vision** | Product pillars without dedicated APIs. |

---

## Architecture

The backend follows **lightweight domain-driven design**: high cohesion inside modules, low coupling between them, with **Plan** as the aggregate root of execution and **UserContext** as the canonical execution context.

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
│   │   ├── execution/       # Execution Engine, FrictionEngine, substitution, TODAY
│   │   ├── context/         # UserContext aggregate
│   │   ├── pillars/         # User-defined pillars seeding helpers
│   │   ├── planner/         # Schedule / day blocks (feeds execution)
│   │   ├── nutrition/       # Macros, catalog, suggest, shopping
│   │   ├── workouts/        # Scaffold (models live under models/plan)
│   │   ├── habits/          # Scaffold (routes + execution modules own behavior)
│   │   ├── progress/        # Scaffold (progress routes on Plan)
│   │   └── ai/              # Scaffold (PlanProposal created by friction/user today)
│   ├── integrations/        # Placeholder for LLM / email providers
│   ├── utils/
│   └── routes/              # Endpoint handlers by surface
├── alembic/                 # Migrations
├── docs/domain/             # Canonical domain model
├── docs/product/            # Product direction & evolution
├── tests/
├── Dockerfile
└── docker-compose.yml
```

Domain reference:

- [Domain model](backend/docs/domain/DOMAIN.md)
- [Gap analysis](backend/docs/domain/GAP_ANALYSIS.md)
- [Migration plan](backend/docs/domain/MIGRATION_PLAN.md)
- [Product direction](backend/docs/product/PRODUCT_DIRECTION.md) — Execution Psychology (canonical)
- [Product evolution](backend/docs/product/PRODUCT_EVOLUTION.md) — TODAY as Execution Engine; mental journey over modules

**Layering:** Models hold structure and simple invariants; repositories load aggregates; **services** own use cases (rebuild TODAY, build UserContext, analyze friction, apply visual replace). Routes stay thin.

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
- Plan CRUD (`goal_type`, duration, status) — life **Goal** entity not separate yet
- **UserContext** aggregate (`GET/PATCH /context`); onboarding is a producer
- **Execution Engine**: Plan + UserContext + date → TODAY (`/plans/{id}/today`, `/execution/today`, `/execution/modules`)
- **ExecutionItems** + **DynamicExecutionItems** on a Plan
- **ExecutionLog** — optional exception logging (silence = on plan)
- **Visual Replace** API (`/execution-items/{id}/alternatives`, `/replace`)
- **FrictionEngine** v0 → creates **PlanProposal**s (`POST /execution-items/friction/analyze`)
- **PlanProposal** list/create + accept/reject **status** (apply-on-accept not wired)
- User-defined **Pillars** CRUD
- Habits on a Plan + TODAY projection
- Progress entries (weight, adherence)
- Nutrition module: meals, daily slots, macro targets via `/goals`, recipe library, meal suggest, shopping list
- Profile onboarding with BMR/TDEE and macro distribution (syncs UserContext)
- Workout **domain models** only (program → days → exercises)
- Config for `DATABASE_URL`, CORS, optional migrate-on-startup
- Docker Compose (API + Postgres)

### In progress
- Domain alignment (life **Goal** entity, NutritionPlan naming, tighter Plan ↔ nutrition day binding)
- Workout **services and HTTP APIs** on top of existing models
- PlanProposal **apply** when status → accepted
- Richer TODAY merge of meals + workouts as first-class execution modules

### Planned — Product
- Canvas UX for Replace / proposals (backend cards already exist)
- Negotiation Count / decisions avoided (product concept)
- Daily Insight + lightweight knowledge module (one idea → one action; never a feed)
- Personal experiments (time-boxed trials; experience before explanation)
- Identity-based reinforcement (not streak theater as the primary reward)
- Full AI Coach (**LLM** generate Plan + constraint-aware proposals—not chat-first renegotiation)
- Stronger adaptation rules (weekly reviews beyond FrictionEngine v0)
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
| Plans | `/plans` | Aggregate root: CRUD, habits, pillars, TODAY, progress |
| Execution catalog | `/plans/{id}/execution-items`, `/dynamic-items`, `/proposals` | Plan actions, one-offs, reviewable proposals |
| Execution Engine | `/plans/{id}/today`, `/execution/today`, `/execution/modules` | Deterministic TODAY projection |
| Execution items (global) | `/execution-items` | Exception **logs**, **alternatives** / **replace**, **friction/analyze** |
| UserContext | `/context` | Canonical execution context (`GET` / `PATCH`) |
| Nutrition days | `/meal-plans` | Legacy name for daily meal structure (domain: NutritionDay) |
| Meals / library / suggest / shopping | `/meals`, `/library`, `/suggest`, `/shopping-list` | Nutrition toolkit |
| Daily macros | `/goals` | Nutrition macro targets **only**—not life Goals |
| Onboarding | `/onboarding` | Profile + energy/macro baseline; producer of UserContext |

Explore the live contract at `/docs` (OpenAPI).

---

## Contributing

Contributions that respect the domain model are welcome:

1. Read [`docs/domain/DOMAIN.md`](backend/docs/domain/DOMAIN.md) and [`docs/product/PRODUCT_DIRECTION.md`](backend/docs/product/PRODUCT_DIRECTION.md).
2. Keep **Plan** as the execution root; don’t introduce competing “plan” nouns for meal days.
3. Put use cases in **services**, not fat route handlers.
4. Add or update tests with behavior changes.
5. Prefer reviewable **PlanProposal**s for system/AI mutations; do not auto-mutate the Plan from chat or silent agents.
6. Apply the product gate: reduce friction / execute TODAY / reinforce discipline or awareness / cut decision fatigue—or don’t build it.

---

## License

Proprietary / TBD — update this section when you publish a license.

---

**Life Planner** — minimize self-negotiation. Decide once. Execute TODAY.
