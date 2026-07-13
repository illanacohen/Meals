# Product Direction — Execution Psychology

Canonical product specification for Life Planner.  
This is **philosophy and direction**, not a backlog of tickets. Implementation follows only when a concept is designed and approved.

Related: [Domain model](../domain/DOMAIN.md) · [README](../../../README.md)

---

## What this product is (and is not)

The current codebase centers Plans, TODAY, nutrition, habits, and workouts. That is the **first wedge**, not the identity.

Life Planner must not become another health tracker.

**Purpose:** help users consistently execute the life they want to live.

People already know they should eat better, exercise, save, sleep, and stop procrastinating. The bottleneck is **friction**—daily self-negotiation against decisions already made.

The application exists to **reduce that friction**.

---

## Core philosophy

| Belief | Implication |
|--------|-------------|
| Execution is a skill | The product trains execution, not knowledge dumps |
| Discipline is trainable | Systems and pre-decisions beat willpower theater |
| Motivation is unreliable | Do not depend on pep talks or streak panic |
| Consistency comes from fewer daily decisions | Pre-decide in the Plan; execute in TODAY |

The product should constantly answer one question:

> **What is the next action that moves me toward my goal?**

Everything else is secondary.

Canonical mission:

> Life Planner is not designed to tell people what to do. It helps them build enough clarity that executing their own decisions becomes easier than renegotiating them.

Shorthand: **Minimize self-negotiation.**

---

## Knowledge as a first-class module

Users often fail not only from friction but from not *feeling why* a behavior matters. Lightweight learning can change willingness to act.

**Not:** long podcasts, endless feeds, TikTok-style content.

**Instead:**

- curated short clips
- key insights
- practical concepts
- actionable lessons
- quotes
- explanations under ~two minutes

**Objective is behavior change, not education.** Knowledge always connects to execution and **ends with an action**.

Example: struggle to wake up → one neuroscience insight on morning light / circadian rhythm → concrete action (get outside light), not generic motivation.

**Daily Insight rule:** at most **one** idea per day. Then the user leaves the app and lives.

Experience before explanation: prefer short **personal experiments** (“try X for 7 days; observe energy/mood”) over “do this because an authority said so.”

Status: **product direction** — not shipped.

---

## Reduce AI negotiation (plan as canvas)

Chat-first AI creates a new negotiation loop (“not yogurt… not that either…”).

Desired model:

1. AI (or system) drafts a plan.
2. User refines **visually**.
3. Each meal / ingredient / task can be **replaced**.
4. Replacements respect constraints: allergies, intolerances, preferences, calories, macros, favorites, pantry (future).
5. System learns preferences over time.

AI creates the first draft; the user edits like a canvas (Figma-like), not like a debate.

Status: **product direction** — coach/chat must not be the primary edit path when this lands.

---

## TODAY reduces decision fatigue

TODAY is the operational center. Opening the app should never leave the user asking “What should I do now?”

TODAY already answers: eat breakfast, prep lunch, train, one work task, water, meditate, sleep routine, …

Completed tasks reduce mental load and create **momentum**.

---

## Build discipline, not streaks

Optimize for **identity**, not streak theater.

Prefer:

- “You proved you can keep a promise.”
- “Today you were the kind of person who trains when motivation is low.”

Avoid making points/streaks the primary reward.

Status: **copy / UX principle** when surfaces ship.

---

## Accept imperfect execution

Perfect adherence is unrealistic. Normalize imperfect days. Progress > perfection. Avoid all-or-nothing framing.

Examples of tone:

- “You completed 60% of today’s execution. That’s enough to keep momentum.”

When building several habits, succeeding at a subset can still be excellent—communicate perspective, not guilt.

---

## Domains (life execution, not fitness-only)

Fitness is the first domain. The product is **life execution**. Every domain uses the same loop:

```text
Goal → Plan → TODAY → Progress → Adaptation
```

**In scope (shipped or designed):** see README Core pillars (Health, Personal Development, Financial Wellbeing, Life Management).

**Possible future pillars** (do not implement until designed into the domain model):

- Work / Deep Work / Learning (beyond habits)
- Relationships
- Household Management
- richer Recovery & Sleep

A pillar is valid only if it **pre-answers micro-decisions** for TODAY.

---

## Product concepts (not features yet)

| Concept | Intent | Non-goal |
|---------|--------|----------|
| **Negotiation Count** | Surface decisions the plan already settled so the user did not reopen them | Guilt score / streak substitute |
| **Plan as canvas** | Constraint-aware replace in 1–2 taps | ChatGPT renegotiation loops |
| **Daily Insight** | One idea → one action | Content feed |
| **Personal experiment** | Time-boxed trial + observe | Authority-based lectures |
| **Identity reinforcement** | Language that reinforces who the user is becoming | Points-first gamification |

---

## Product rule (gate for every feature)

Before implementing anything, ask:

1. Does this **reduce friction**?
2. Does it help the user **execute today’s plan**?
3. Does it reinforce **discipline or self-awareness**?
4. Does it **reduce decision fatigue** (or reopen fewer decisions)?

If the answer is no, it probably does not belong in Life Planner.

---

## Long-term vision

Life Planner is a **personal execution operating system**.

Not an AI chat.  
Not a calorie tracker.  
Not a habit tracker.  
Not a finance app.

A system that helps people become who they want to be by translating long-term goals into meaningful daily actions, reducing friction, reinforcing discipline, and adapting the plan as life changes.
