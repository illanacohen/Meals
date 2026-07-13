"""Visual substitution — structural alternatives, never chat."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.models.context import UserContext
from app.models.execution import ExecutionItem
from app.repositories import execution as execution_repo


@dataclass(frozen=True)
class SubstituteOption:
    """Card-ready alternative for the UI Replace flow."""

    id: str
    title: str
    source_module: str
    metadata: dict[str, Any]
    match_score: float
    reason: str


# Rule catalog: macro-matched food swaps (protein / carbs / fat within tolerance).
_NUTRITION_CATALOG: list[dict[str, Any]] = [
    {'name': 'Greek yogurt', 'protein': 20, 'carbs': 15, 'fat': 5, 'tags': ['dairy']},
    {'name': 'Turkey breast', 'protein': 22, 'carbs': 0, 'fat': 2, 'tags': ['meat']},
    {'name': 'Firm tofu', 'protein': 18, 'carbs': 4, 'fat': 8, 'tags': ['vegan', 'vegetarian']},
    {'name': 'Cottage cheese', 'protein': 21, 'carbs': 6, 'fat': 4, 'tags': ['dairy']},
    {'name': 'Egg whites (4)', 'protein': 14, 'carbs': 1, 'fat': 0, 'tags': ['vegetarian']},
    {'name': 'Canned tuna', 'protein': 22, 'carbs': 0, 'fat': 1, 'tags': ['fish']},
    {'name': 'Chicken breast', 'protein': 25, 'carbs': 0, 'fat': 3, 'tags': ['meat']},
    {'name': 'Skyr', 'protein': 19, 'carbs': 8, 'fat': 0, 'tags': ['dairy']},
    {'name': 'Tempeh', 'protein': 19, 'carbs': 9, 'fat': 7, 'tags': ['vegan', 'vegetarian']},
    {'name': 'Lean beef strips', 'protein': 23, 'carbs': 0, 'fat': 6, 'tags': ['meat']},
    {'name': 'Protein shake (whey)', 'protein': 24, 'carbs': 3, 'fat': 1, 'tags': ['dairy']},
    {'name': 'Protein shake (plant)', 'protein': 20, 'carbs': 5, 'fat': 2, 'tags': ['vegan', 'vegetarian']},
    {'name': 'Smoked salmon', 'protein': 18, 'carbs': 0, 'fat': 7, 'tags': ['fish']},
    {'name': 'Edamame bowl', 'protein': 17, 'carbs': 14, 'fat': 8, 'tags': ['vegan', 'vegetarian']},
    {'name': 'Lentil mash', 'protein': 16, 'carbs': 20, 'fat': 1, 'tags': ['vegan', 'vegetarian']},
]

_WORKOUT_CATALOG: list[dict[str, Any]] = [
    {'name': 'Bodyweight squats', 'muscle': 'legs', 'equipment': [], 'duration_minutes': 20},
    {'name': 'Goblet squat', 'muscle': 'legs', 'equipment': ['dumbbells'], 'duration_minutes': 25},
    {'name': 'Walking lunges', 'muscle': 'legs', 'equipment': [], 'duration_minutes': 20},
    {'name': 'Push-up variations', 'muscle': 'push', 'equipment': [], 'duration_minutes': 15},
    {'name': 'Dumbbell bench press', 'muscle': 'push', 'equipment': ['dumbbells'], 'duration_minutes': 30},
    {'name': 'Resistance-band rows', 'muscle': 'pull', 'equipment': ['bands'], 'duration_minutes': 20},
    {'name': 'Pull-ups / assisted', 'muscle': 'pull', 'equipment': ['pull-up bar'], 'duration_minutes': 20},
    {'name': 'Brisk walk 20 min', 'muscle': 'cardio', 'equipment': [], 'duration_minutes': 20},
    {'name': 'Stationary bike', 'muscle': 'cardio', 'equipment': ['bike'], 'duration_minutes': 25},
    {'name': 'Mobility flow', 'muscle': 'recovery', 'equipment': [], 'duration_minutes': 15},
]

_MACRO_TOLERANCE = {'protein': 6, 'carbs': 10, 'fat': 5}


def _option_id(title: str, module: str) -> str:
    digest = hashlib.sha1(f'{module}:{title}'.encode()).hexdigest()[:10]
    return f'alt-{module}-{digest}'


def _restriction_blocked(tags: list[str], user_context: UserContext | None) -> bool:
    if user_context is None:
        return False
    bans = {
        *(user_context.dietary_restrictions or []),
        *(user_context.food_intolerances or []),
        *(user_context.disliked_foods or []),
    }
    bans_l = {str(b).lower() for b in bans}
    if 'vegetarian' in bans_l and any(t in ('meat', 'fish') for t in tags):
        return True
    if 'vegan' in bans_l and any(t in ('meat', 'fish', 'dairy') for t in tags):
        return True
    if 'lactose' in bans_l and 'dairy' in tags:
        return True
    if any(t.lower() in bans_l for t in tags):
        return True
    return False


def _macro_distance(src: dict[str, Any], cand: dict[str, Any]) -> float | None:
    total = 0.0
    for key, tol in _MACRO_TOLERANCE.items():
        s = float(src.get(key) or 0)
        c = float(cand.get(key) or 0)
        if abs(s - c) > tol:
            return None
        total += abs(s - c)
    return total


class SubstitutionService:
    """Produce visual Replace cards and apply a chosen substitute to the Plan."""

    def get_smart_substitutes(
        self,
        db: Session,
        execution_item_id: int,
        user_context: UserContext | None = None,
        *,
        limit: int = 3,
    ) -> list[SubstituteOption]:
        item = db.get(ExecutionItem, execution_item_id)
        if item is None:
            raise ValueError('ExecutionItem not found')

        meta = dict(item.item_metadata or {})
        module = (item.source_module or 'planner').lower()

        if module == 'nutrition':
            options = self._nutrition_subs(item, meta, user_context)
        elif module == 'workouts':
            options = self._workout_subs(item, meta, user_context)
        else:
            options = self._generic_subs(item, meta, user_context)

        options.sort(key=lambda o: (-o.match_score, o.title))
        return options[:limit]

    def apply_substitute(
        self,
        db: Session,
        execution_item_id: int,
        alternative_id: str,
        user_context: UserContext | None = None,
        *,
        as_proposal: bool = False,
    ) -> tuple[ExecutionItem, Any]:
        """
        Apply a chosen visual substitute.

        Default: mutate the ExecutionItem for the rest of the Plan (user picked a card).
        as_proposal=True: only create a pending PlanProposal (no mutation).
        """
        item = db.get(ExecutionItem, execution_item_id)
        if item is None:
            raise ValueError('ExecutionItem not found')

        options = self.get_smart_substitutes(db, execution_item_id, user_context, limit=12)
        chosen = next((o for o in options if o.id == alternative_id), None)
        if chosen is None:
            raise ValueError('Alternative not found for this execution item')

        payload = {
            'type': 'replace',
            'execution_item_id': item.id,
            'from_title': item.title,
            'to_title': chosen.title,
            'alternative_id': chosen.id,
            'metadata': chosen.metadata,
            'reason': chosen.reason,
        }

        if as_proposal:
            proposal = execution_repo.create_proposal(
                db,
                item.plan_id,
                status='pending',
                rationale=chosen.reason,
                payload=payload,
                created_by='user',
            )
            return item, proposal

        previous = {
            'title': item.title,
            'metadata': dict(item.item_metadata or {}),
            'description': item.description,
        }
        item.title = chosen.title
        merged_meta = {**(item.item_metadata or {}), **chosen.metadata, 'substituted_from': previous['title']}
        if chosen.metadata.get('preferred_block') or chosen.metadata.get('preferred_time'):
            schedule = dict(item.schedule_rule or {})
            if chosen.metadata.get('preferred_block'):
                schedule['preferred_block'] = chosen.metadata['preferred_block']
            if chosen.metadata.get('preferred_time'):
                schedule['preferred_time'] = chosen.metadata['preferred_time']
            if chosen.metadata.get('friction') is not None:
                schedule['friction'] = chosen.metadata['friction']
            item.schedule_rule = schedule
        if chosen.metadata.get('estimated_duration') is not None:
            item.estimated_duration = int(chosen.metadata['estimated_duration'])
        item.item_metadata = merged_meta
        proposal = execution_repo.create_proposal(
            db,
            item.plan_id,
            status='accepted',
            rationale=f'User replaced via visual substitute: {previous["title"]} → {chosen.title}',
            payload={**payload, 'previous': previous},
            created_by='user',
        )
        db.flush()
        return item, proposal

    def _nutrition_subs(
        self,
        item: ExecutionItem,
        meta: dict[str, Any],
        user_context: UserContext | None,
    ) -> list[SubstituteOption]:
        src_name = str(meta.get('name') or item.title)
        options: list[SubstituteOption] = []
        for cand in _NUTRITION_CATALOG:
            if cand['name'].lower() == src_name.lower():
                continue
            if _restriction_blocked(list(cand.get('tags') or []), user_context):
                continue
            dist = _macro_distance(meta, cand)
            if dist is None and not any(k in meta for k in ('protein', 'carbs', 'fat')):
                # No macros on item — still offer catalog filtered by restrictions.
                dist = 50.0
            if dist is None:
                continue
            score = max(0.0, 100.0 - dist * 4)
            options.append(
                SubstituteOption(
                    id=_option_id(cand['name'], 'nutrition'),
                    title=cand['name'],
                    source_module='nutrition',
                    metadata={
                        'name': cand['name'],
                        'protein': cand['protein'],
                        'carbs': cand['carbs'],
                        'fat': cand['fat'],
                        'tags': cand['tags'],
                    },
                    match_score=score,
                    reason='Macro-matched substitute for visual Replace',
                )
            )
        return options

    def _workout_subs(
        self,
        item: ExecutionItem,
        meta: dict[str, Any],
        user_context: UserContext | None,
    ) -> list[SubstituteOption]:
        muscle = str(meta.get('muscle') or meta.get('focus') or 'legs').lower()
        owned = {str(e).lower() for e in (user_context.equipment or [])} if user_context else set()
        gym = bool(user_context.gym_access) if user_context and user_context.gym_access is not None else True
        injuries = {str(i).lower() for i in (user_context.injuries or [])} if user_context else set()

        options: list[SubstituteOption] = []
        for cand in _WORKOUT_CATALOG:
            if cand['name'].lower() == item.title.lower():
                continue
            if cand['muscle'] != muscle and muscle not in ('any', 'full'):
                # Prefer same muscle; still allow recovery/cardio as softer swaps later
                if cand['muscle'] not in (muscle, 'recovery'):
                    continue
            needed = [e.lower() for e in (cand.get('equipment') or [])]
            if needed and not gym and not set(needed).issubset(owned):
                continue
            if any(inj in cand['name'].lower() or inj in muscle for inj in injuries):
                continue
            score = 90.0 if cand['muscle'] == muscle else 70.0
            if not needed:
                score += 5.0
            options.append(
                SubstituteOption(
                    id=_option_id(cand['name'], 'workouts'),
                    title=cand['name'],
                    source_module='workouts',
                    metadata={
                        'name': cand['name'],
                        'muscle': cand['muscle'],
                        'equipment': cand['equipment'],
                        'duration_minutes': cand['duration_minutes'],
                    },
                    match_score=score,
                    reason='Equipment- and focus-matched workout substitute',
                )
            )
        return options

    def _generic_subs(
        self,
        item: ExecutionItem,
        meta: dict[str, Any],
        user_context: UserContext | None,
    ) -> list[SubstituteOption]:
        """Habits / planner: structural schedule and friction alternatives (cards, not chat)."""
        rule = dict(item.schedule_rule or {})
        current_block = str(rule.get('preferred_block') or 'execution')
        blocks = ['high_performance', 'execution', 'recovery']
        options: list[SubstituteOption] = []
        for block in blocks:
            if block == current_block:
                continue
            title = f'{item.title} ({block.replace("_", " ")})'
            options.append(
                SubstituteOption(
                    id=_option_id(f'{item.id}:{block}', item.source_module or 'planner'),
                    title=item.title,
                    source_module=item.source_module or 'planner',
                    metadata={
                        **meta,
                        'preferred_block': block,
                        'friction': max(1, int(rule.get('friction') or 3) - (1 if block == 'recovery' else 0)),
                        'display_label': title,
                    },
                    match_score=80.0 if block == 'recovery' else 65.0,
                    reason=f'Move to {block.replace("_", " ")} block to cut friction',
                )
            )
        # Shorter version card
        options.append(
            SubstituteOption(
                id=_option_id(f'{item.id}:short', item.source_module or 'planner'),
                title=f'{item.title} (10 min version)',
                source_module=item.source_module or 'planner',
                metadata={
                    **meta,
                    'estimated_duration': 10,
                    'non_negotiable_minimum': True,
                },
                match_score=75.0,
                reason='Shorter non-negotiable version for high-friction days',
            )
        )
        if user_context and user_context.preferred_training_time:
            options.append(
                SubstituteOption(
                    id=_option_id(f'{item.id}:pref-time', item.source_module or 'planner'),
                    title=item.title,
                    source_module=item.source_module or 'planner',
                    metadata={
                        **meta,
                        'preferred_time': user_context.preferred_training_time.isoformat(),
                    },
                    match_score=72.0,
                    reason='Align with preferred training time from UserContext',
                )
            )
        return options


substitution_service = SubstitutionService()
