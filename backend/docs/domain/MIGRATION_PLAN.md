# Migration Plan — Align Schema & Code to Domain

Prerequisite: approved [`DOMAIN.md`](DOMAIN.md), gaps in [`GAP_ANALYSIS.md`](GAP_ANALYSIS.md).

**This document is the implementation blueprint.** Do not run large renames until each wave is scheduled. Prefer additive migrations (new tables/columns) before destructive renames.

## Principles

1. **Expand–migrate–contract:** add new shapes → backfill → switch reads/writes → drop legacy.
2. **One active Plan rule** enforced in services before DB uniqueness if multi-row history needed.
3. **Keep APIs working** during waves via aliases (`/meal-plans` stays until NutritionDay clients exist).
4. **No AI chat tables** — only `PlanProposal` when AI lands.
5. **Tests green after every wave.**

---

## Wave 0 — Documentation & language freeze (done in Phase 1)

- [x] Publish DOMAIN.md, GAP_ANALYSIS.md, MIGRATION_PLAN.md
- [ ] README links to `docs/domain/`
- [ ] Team rule: never call nutrition day “Plan” in new code/comments

**Deliverable:** Shared vocabulary. No schema change required beyond docs.

---

## Wave 1 — Goal entity + Plan enrichment (additive)

### Schema
- Create `goals`:
  - `id`, `user_profile_id` (FK, later `user_id`), `type`, `target_metric`, `target_value`, `unit`, `deadline`, `status`, timestamps
- Alter `plans`:
  - `goal_id` nullable FK → `goals`
  - `enabled_modules` JSON/text flags: `{nutrition, workouts, habits, progress}`
- Backfill: for each Plan, create Goal from `plan.goal_type` + profile; set `plans.goal_id`
- Keep `plans.goal_type` temporarily (read fallback)

### Code
- Models: `Goal`
- Package: `services/goals/`, `repositories/goal.py`
- Plan create/update accepts `goal_id` or creates Goal inline
- Do **not** remove `UserProfile.goal` yet

### Tests
- Creating a Plan creates/links a Goal
- Listing plans returns goal reference

### Rollback
- Drop `goal_id` / `goals` table; ignore new columns

---

## Wave 2 — NutritionPlan + bind days to Plan

### Schema
- Create `nutrition_plans`:
  - `id`, `plan_id` UNIQUE FK → `plans`
  - macro targets (calories, protein, fat, carbs, fiber)
  - `meals_per_day`, `mode` (`structured|flexible`), distribution JSON optional
- Alter `meal_plans` (still table name in this wave):
  - Make `goal_plan_id` **NOT NULL** after backfill (or add `nutrition_plan_id` FK and prefer it)
  - Backfill: for each Plan missing NutritionPlan, create one from latest `daily_goals` or onboarding defaults
  - Attach orphan `meal_plans` to active Plan or a synthetic “legacy” Plan
- Deprecation path for `daily_goals`:
  - Stop writing new DailyGoals from onboarding once NutritionPlan exists
  - Read path: NutritionPlan targets first, DailyGoal fallback

### Code
- Model `NutritionPlan`
- Onboarding writes NutritionPlan under new/active Plan
- Validate/summary services prefer NutritionPlan targets
- Route `/goals` (DailyGoal): mark deprecated in docs; add `/plans/{id}/nutrition` for targets

### Tests
- Plan + NutritionPlan 1:1
- Meal day requires plan link
- Summary/validate use NutritionPlan

### Rollback
- Keep DailyGoal writers; drop nutrition_plans

---

## Wave 3 — Rename NutritionDay & Recipe (contract)

### Schema (Alembic rename or new tables + copy)
- Rename conceptual `MealPlan` → **NutritionDay**
  - Preferred: rename table `meal_plans` → `nutrition_days`, column `goal_plan_id` → `plan_id` or `nutrition_plan_id`
  - Update `meal_slots.plan_id` FK name carefully (slot’s parent day id)
- Rename `meal_templates` → `recipes`, `meal_template_items` → `recipe_items`
- Optional: `meals.recipe_id` nullable FK

### Code / API
- ORM class renames with temporary aliases (`MealPlan = NutritionDay`) for one release
- Router: keep `/meal-plans` as alias; add `/plans/{id}/nutrition/days`
- Library routes: `/library` → document as recipes; optional `/recipes`

### Tests
- Full nutrition suite against new names
- Alias routes still pass

### Rollback
- Reverse renames (painful) — only after Wave 2 stable

---

## Wave 4 — DailyTask unified projection

### Schema
- No mandatory change; optional `scheduled_time` on `daily_tasks`
- Ensure unique constraint still fits meal titles (may need `source_id` in uniqueness — already has type+title)

### Code
- Extend [`services/planner/daily.py`](../../app/services/planner/daily.py):
  - Habits (existing)
  - Meals from NutritionDay slots for date
  - WorkoutDay for calendar mapping (week_number + day_of_week vs plan start)
- Toggle completion:
  - `habit` → upsert HabitCompletion
  - `meal` / `workout` → flag on DailyTask only until session/log entities exist

### Tests
- TODAY includes habit + meal + workout when present
- Idempotent rebuild

---

## Wave 5 — CheckIn + PlanProposal + Exercise catalog

### Schema
- `check_ins`: plan_id, date, period (`daily|weekly`), energy, sleep_score, negotiations, notes, blockers JSON
- `plan_proposals`: plan_id, status, rationale, payload JSON, created_by, timestamps
- `exercises`: name, muscle_group, equipment, level
- Alter `workout_exercises`: nullable `exercise_id` FK

### Code
- `services/planner` CheckIn use cases
- `services/adaptation` builds PlanProposal from rules (no LLM yet)
- `services/ai` fills PlanProposal from LLM later
- Accept proposal orchestrates nutrition/habits/workouts services

### Tests
- Proposal accept updates NutritionPlan macros via service
- Reject leaves plan unchanged

---

## Wave 6 — ShoppingListSnapshot (optional) + DailyGoal removal

### Schema
- `shopping_list_snapshots`: plan_id, start_date, end_date, lines JSON, created_at
- Drop or archive `daily_goals` after zero reads

### Code
- Existing compute path unchanged; POST save snapshot

---

## Wave 7 — Identity split (when auth arrives)

### Schema
- `users` table (auth subject)
- `user_profiles.user_id` FK
- Re-point Goal/Plan FKs to `users`
- Remove duplicated goal fields from profile

### Code
- `services/identity`
- Auth middleware; multi-tenant filters on all plan queries

---

## Suggested order of PR slices

| PR | Wave | Risk |
|----|------|------|
| Docs only | 0 | None |
| Goal + plan.goal_id | 1 | Low |
| NutritionPlan + onboarding write path | 2 | Medium |
| Rename NutritionDay/Recipe | 3 | Medium–High |
| Unified TODAY | 4 | Medium |
| CheckIn + PlanProposal + Exercise | 5 | Medium |
| Snapshot + drop DailyGoal | 6 | Low–Medium |
| Auth User | 7 | High (defer) |

---

## Non-goals for migration waves

- New frontend screens
- Full AI coach product
- Renaming `/plans` away from master Plan
- Merging Strong-like workout logging (`WorkoutSession`) before Wave 5

---

## Definition of done (domain alignment)

- [ ] No new code calls nutrition day “Plan”
- [ ] Every NutritionDay belongs to a Plan via NutritionPlan
- [ ] Macro targets live on NutritionPlan (DailyGoal deprecated)
- [ ] Goal entity exists; Plan references it
- [ ] DailyTask rebuilt from habits + meals + workouts
- [ ] PlanProposal is the only AI/system mutation contract
- [ ] Gap table in GAP_ANALYSIS.md shows zero “High” severities remaining
