# Product Evolution Proposal — From Modules to Mental Journey

**Status:** Approved direction for product design. Not an implementation backlog.  
**Parent:** [PRODUCT_DIRECTION.md](PRODUCT_DIRECTION.md) (philosophy).  
**Does not replace:** [DOMAIN.md](../domain/DOMAIN.md) until a dedicated domain wave redesigns entities.

---

## Paradigm shift

| Today (codebase) | Target (product) |
|------------------|------------------|
| Organized by **data entities** (Plan, MealPlan, Habit, Workout…) | Organized by the user’s **mental journey**: decide → face friction → execute → reflect → prepare tomorrow |
| TODAY = generated checklist | TODAY = **Execution Engine** |
| Modules feel like separate trackers | Same loop for every pillar; planner does not care if a task is food or finance |
| AI as conversation | AI drafts; user **refines visually**; AI coaches execution |

**Objective is not** to add dozens of features.  
**Objective is** to redesign the flow so the app actively helps the user execute difficult things.

Differentiator:

> Life Planner does not help organize tasks. It reduces the friction between who you want to become and the actions you must take today to become that person.

---

## Mental journey (UX spine)

```text
Goal clarity
    → Plan (pre-decided)
        → TODAY (execution engine)
            → Why / Insight (reduce resistance)
            → Complete / mark friction
            → Reflection (no guilt)
            → Win Tomorrow (cut next-day friction)
                → Progress + Adaptation
```

Entity modules (nutrition, finance, …) plug into this spine. They are not the home screen.

---

## 1. Execution Engine (TODAY evolved)

TODAY is no longer “just a checklist.” It is the application’s **execution engine**.

Each actionable item carries execution metadata, for example:

```json
{
  "title": "Prepare lunch",
  "pillar": "nutrition",
  "friction": 6,
  "energy": "medium",
  "duration_minutes": 20,
  "priority": 4,
  "recurring": true,
  "completed": false,
  "reward": null,
  "why": "Preparing food now prevents impulsive eating later."
}
```

Fields (logical):

| Field | Role |
|-------|------|
| `duration` / estimated minutes | Scheduling & load |
| `friction` (planned) | Placement / order (aligns with existing Daily Planner friction) |
| `energy` | Match to day blocks / capacity |
| `pillar` | Domain tag only—not a separate home |
| `priority` | Ordering inside blocks |
| `recurring` \| one-time | Seeding |
| `completed` | State |
| `reward` (optional) | Identity cue, not points spam |
| `why` | Practical explanation (see §2) |

**Future:** engine reorders TODAY dynamically from friction, energy, time, and progress—not fixed static lists.

**Relation to code today:** [`DailyTask`](../../app/models/plan.py) + planner engine already have friction/priority/duration/block on PlanTask/DailyTask in part. Evolution extends metadata (`why`, `energy`, user-reported friction) and treats TODAY as the product center—not a side view of habits.

---

## 2. Why (on actions)

Every meaningful action may include a short **practical** why—not motivational quotes.

```text
Drink water
Why: Proper hydration improves attention and reduces perceived fatigue.
```

Goal: lower resistance through understanding. Knowledge snippets can supply copy; the action still owns the CTA.

---

## 3. Knowledge Library (module)

Independent of AI chat. First-class product module:

```text
Knowledge
├── Topics
├── Insights
├── Clips
├── Quotes
└── Actionable lessons
```

Item shape (logical): title, author, source, duration, summary, practical takeaway, related pillars, related habits/actions.

Eventually TODAY may surface **one** relevant insight (Daily Insight rule from product direction). Never a feed.

---

## 4. Visual editing (replace conversation)

Especially for meals (then all plan items):

- Replace  
- Duplicate  
- Remove  
- Lock  

Example: Chicken → Replace → Turkey / lean beef / fish / tofu — filtered by preferences (§5).

AI generates the first draft; user refines on a canvas. No re-explaining lactose in chat.

---

## 5. Preference Engine

Persist preferences permanently and inject them into every planner/AI draft:

- Likes / dislikes  
- Allergies / intolerances  
- Favorite meals / exercises  
- Equipment, cooking time, budget  

User should never re-negotiate the same constraint. Overlaps partially with `UserProfile` / food preferences today—evolution makes this the **single preference brain** for all pillars.

**Implementation home:** preferences/constraints now live on the **UserContext** aggregate (`services/context`). Preference Engine UX can evolve on top of UserContext without new profile tables.

---

## 6. Friction Tracking (learned)

Planned friction (engine input) ≠ **experienced** friction (user feedback).

After or on a task, user can mark: Easy / Neutral / Hard / Very Hard (or 1–10).

Planner adapts future plans (e.g. running 9/10 → schedule earlier / shorter / substitute). Feeds Negotiation Count / adaptation later.

---

## 7. Reflection (instead of guilt)

Lightweight end-of-day reflection focused on **execution**, not emotional journaling:

- What created the most friction today?  
- What became easier than expected?  
- What would make tomorrow easier?  

Maps conceptually to future CheckIn—not a diary product.

---

## 8. Win Tomorrow

End of day: generate **one** preparation task that cuts tomorrow’s friction.

Examples: prep lunch, lay out gym clothes, fill water bottle, charge laptop, set breakfast.

Belongs in Recovery / Life Management block; sticky into next TODAY.

---

## 9. Identity-based feedback

Do not lead with generic streaks. Reinforce identity and behavior:

- “You kept a promise to yourself.”  
- “You executed despite low motivation.”  
- “You reduced friction before it became an excuse.”  

Reward behavior, not mere attendance.

---

## 10. Configurable Pillars

Remove fitness-as-center assumption. Generic **Pillar** model; catalog examples:

Nutrition, Training, Work, Finance, Learning, Relationships, Home, Recovery, Mindfulness, Custom.

Every pillar shares:

```text
Goal → Plan → TODAY → Progress → Adaptation
```

The execution engine treats all tasks as today’s work; pillar is metadata.

**Note:** Relationships / Home / Mindfulness stay **out of schema** until designed—list here is product vocabulary only.

---

## 11. Micro Wins

Large goals decompose into minimal activation-energy steps:

```text
Goal: Improve finances
Today: Open banking app
Tomorrow: Categorize last week’s expenses
Next: Create one savings rule
```

Planner progressively lowers the first step of resistance.

---

## 12. Future AI responsibilities

AI is an **execution coach**, not a chatbot:

- build / simplify plans  
- detect friction and patterns  
- recommend easier alternatives  
- explain why  
- adapt future plans  
- reduce decision fatigue  

Primary mutation path remains reviewable proposals + canvas edits—not open-ended chat as the product.

---

## Mapping: mental journey → today’s architecture

| Journey step | Current rough map | Evolution gap |
|--------------|-------------------|---------------|
| Goal | `Plan.goal_type` / future Goal entity | Explicit Goal aggregate |
| Plan | `Plan` + PlanTasks / nutrition / workouts | Pillar-agnostic Plan slices |
| TODAY / engine | `DailyTask` + day blocks | Full metadata, dynamic reorder, why |
| Why / Knowledge | — | New knowledge bounded context |
| Preferences | `UserProfile` partial → **UserContext** | Preference Engine (on UserContext) |
| Friction learned | Planned friction only | User-reported friction + adapt |
| Reflection | — | CheckIn-style, execution-focused |
| Win Tomorrow | — | Seeded PlanTask / DailyTask |
| Identity copy | — | UX layer |
| Micro wins | — | Goal → action decomposition |
| Visual replace | Meal CRUD only | Constraint-aware replace UX |
| AI coach | Scaffold | PlanProposal + canvas |

---

## Implementation stance (for Cursor / team)

1. **Do not** implement all twelve items in one wave.  
2. Any feature must pass the [product gate](PRODUCT_DIRECTION.md#product-rule-gate-for-every-feature).  
3. Prefer evolving **TODAY → Execution Engine** + **Why** + **Preferences** before new life pillars.  
4. Knowledge, Win Tomorrow, Reflection, Micro Wins, and visual Replace are **design-then-build** waves.  
5. Domain migrations stay expand–migrate–contract per [MIGRATION_PLAN.md](../domain/MIGRATION_PLAN.md).

---

## Acceptance of this proposal (docs)

- [x] Paradigm documented: mental journey over entity collection  
- [x] Twelve evolution themes specified with non-goals where needed  
- [x] Linked to Execution Psychology parent doc  
- [ ] Domain entity redesign (Pillar, KnowledgeItem, PreferenceProfile, …) — separate design approval  
- [ ] Code waves — only after per-theme design approval
