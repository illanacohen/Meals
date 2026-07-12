# Gap Analysis — Current Code vs Approved Domain

Date: 2026-07-12  
Scope: read-only comparison of `backend` against [`DOMAIN.md`](DOMAIN.md).  
No feature work; this document drives [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md).

## Summary

| Status | Count | Notes |
|--------|------:|-------|
| Aligned ORM | 10 | Plan, Habit, HabitCompletion, Workout*, DailyTask, ProgressEntry, Meal, MealItem |
| Rename / reshape | 5 | UserProfile→User+Profile, MealPlan→NutritionDay, MealTemplate→Recipe, DailyGoal→NutritionPlan targets |
| Missing ORM | 7 | User, Goal, NutritionPlan, Exercise catalog, CheckIn, PlanProposal, ShoppingListSnapshot |
| Extra structural | 2 | MealSlot (keep), MealTemplateItem (→ RecipeItem) |

Strongest coverage: **Plan + habits + meals**. Weakest: **identity split, Goal entity, nutrition policy container, AI proposal, check-ins**.

---

## 1. Current ORM inventory

### [`app/models/user_profile.py`](../../app/models/user_profile.py)

| Class | Table | FKs |
|-------|-------|-----|
| `UserProfile` | `user_profiles` | — |

### [`app/models/plan.py`](../../app/models/plan.py)

| Class | Table | FKs |
|-------|-------|-----|
| `Plan` | `plans` | `user_profile_id` → `user_profiles` |
| `Habit` | `habits` | `plan_id` → `plans` |
| `HabitCompletion` | `habit_completions` | `habit_id` → `habits` |
| `WorkoutProgram` | `workout_programs` | `plan_id` → `plans` (unique) |
| `WorkoutDay` | `workout_days` | `program_id` → `workout_programs` |
| `WorkoutExercise` | `workout_exercises` | `day_id` → `workout_days` |
| `DailyTask` | `daily_tasks` | `plan_id` → `plans`; `source_id` int (not FK) |
| `ProgressEntry` | `progress_entries` | `plan_id` → `plans` |

### [`app/models/meal.py`](../../app/models/meal.py)

| Class | Table | FKs |
|-------|-------|-----|
| `DailyGoal` | `daily_goals` | — (unique `date`, not plan-scoped) |
| `MealPlan` | `meal_plans` | `goal_plan_id` → `plans` (nullable) |
| `MealSlot` | `meal_slots` | `plan_id` → `meal_plans` |
| `Meal` | `meals` | `slot_id` → `meal_slots` |
| `MealItem` | `meal_items` | `meal_id` → `meals` |
| `MealTemplate` | `meal_templates` | — |
| `MealTemplateItem` | `meal_template_items` | `template_id` → `meal_templates` |

---

## 2. Entity-by-entity gap

| Domain entity | Current state | Gap severity | Action |
|---------------|---------------|--------------|--------|
| **User** | Missing; only `UserProfile` | High | Introduce User (or treat profile as user until auth); stop overloading profile with goal |
| **Goal** | Embedded: `UserProfile.goal`, `Plan.goal_type` | High | New `goals` table; Plan.goal_id FK; migrate strings |
| **Plan** | Present | Low | Add `goal_id`, `enabled_modules`; enforce single `active` |
| **NutritionPlan** | Missing | High | New 1:1 with Plan; absorb macro targets from DailyGoal/onboarding |
| **NutritionDay** | Present as `MealPlan` | Medium | Rename conceptually + table/API later; require Plan link |
| **MealSlot** | Present | None | Keep as structure under NutritionDay |
| **Meal / MealItem** | Present | Low | Optional `recipe_id`; ensure day always under Plan |
| **Recipe / RecipeItem** | Present as MealTemplate* | Medium | Rename; optional plan/user scope |
| **ShoppingListSnapshot** | Computed only (`shopping_list` service) | Low | Optional persist table; keep compute path |
| **WorkoutProgram / Day / Exercise row** | Present | Low | Service layer still scaffold |
| **Exercise (catalog)** | Missing; name string on WorkoutExercise | Medium | New catalog; nullable FK on WorkoutExercise |
| **Habit / HabitCompletion** | Present | Low | Add linchpin / non_negotiable flags when needed |
| **DailyTask** | Present; rebuild from habits only | Medium | Projection must also pull meals + workouts |
| **CheckIn** | Missing | Medium | New model; distinct from ProgressEntry |
| **ProgressEntry** | Present | Low | Move logic into `services/progress` |
| **PlanProposal** | Missing; `services/ai` empty | High | New model before AI features |
| **DailyGoal** | Present, global by date | High | Deprecate in favor of NutritionPlan targets |

---

## 3. Services gap

| Package | Models ready? | Logic ready? | Gap |
|---------|---------------|--------------|-----|
| `nutrition/` | Partial (no NutritionPlan) | Yes (catalog, macros, suggest, shopping, onboarding) | Bind days to Plan; introduce NutritionPlan service |
| `planner/` | DailyTask yes; CheckIn no | Partial (`daily.py` habits only) | Rebuild TODAY from all modules; CheckIn service |
| `habits/` | Yes | Scaffold only | Move habit use cases out of routes |
| `workouts/` | Yes | Scaffold only | CRUD + progression services |
| `progress/` | Yes | Scaffold (route CRUD only) | Adherence metrics service |
| `adaptation/` | No | Missing package | Weekly rules → PlanProposal |
| `ai/` | No PlanProposal | Scaffold | LLM → PlanProposal only |
| `identity/` / `goals/` | No | Missing packages | Split from onboarding |

Legacy shims still re-export nutrition modules from `app/services/*.py` — fine until packages stabilize.

---

## 4. API / routes gap

From [`app/api/router.py`](../../app/api/router.py):

| Prefix | Maps to | Domain fit |
|--------|---------|------------|
| `/plans` | Goal Plan | Correct root |
| `/meal-plans` | MealPlan (nutrition day) | Should become NutritionDay under Plan |
| `/meals`, `/library`, `/suggest`, `/shopping-list` | Nutrition | Keep under nutrition module |
| `/goals` | **DailyGoal macros** | **Naming collision** with domain Goal — rename to `/nutrition/targets` or fold into NutritionPlan |
| `/onboarding` | UserProfile + DailyGoal | Should create User/Goal/Plan + NutritionPlan |

---

## 5. Coupling / rule violations today

1. **`DailyGoal` is global by date**, not owned by a Plan → breaks Plan-first rule.
2. **`MealPlan.goal_plan_id` is nullable** → nutrition days can exist outside any Plan.
3. **`Plan.goal_type` duplicates intention** that belongs on Goal.
4. **`DailyTask` rebuild ignores meals/workouts** → checklist is not the unified HOY yet.
5. **No PlanProposal** → no safe contract for AI/system mutations.
6. **`/goals` means macros**, not Goal entity → ubiquitous language conflict.

---

## 6. Priority to close gaps (for migration plan)

1. **P0 language:** Document + API rename path for DailyGoal vs Goal; freeze “Plan” = master only.
2. **P1 structure:** Goal entity; NutritionPlan; require NutritionDay → Plan; Plan.enabled_modules / goal_id.
3. **P2 projection:** DailyTask rebuild from habits + meals + workouts.
4. **P3 rename polish:** MealTemplate → Recipe; Exercise catalog; CheckIn; PlanProposal; optional ShoppingListSnapshot.

See sequenced steps in [`MIGRATION_PLAN.md`](MIGRATION_PLAN.md).
