"""FrictionEngine — detect exception patterns and emit PlanProposal cards.

Never writes chatbot text. Output is structured proposal payloads the UI can render.
Silence (no ExecutionLog) is treated as on-plan; only logged exceptions feed analysis.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, time, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.models.context import UserContext
from app.models.execution import ExecutionItem, ExecutionLog, PlanProposal
from app.models.plan import Plan
from app.repositories import execution as execution_repo


def _parse_preferred_time(item: ExecutionItem) -> time | None:
    rule = item.schedule_rule or {}
    raw = rule.get('preferred_time') or (item.item_metadata or {}).get('preferred_time')
    if raw is None:
        return None
    if isinstance(raw, time):
        return raw
    try:
        return time.fromisoformat(str(raw))
    except ValueError:
        return None


def _minutes(t: time) -> int:
    return t.hour * 60 + t.minute


def _median_time(times: list[time]) -> time:
    mins = sorted(_minutes(t) for t in times)
    mid = mins[len(mins) // 2]
    return time(hour=mid // 60, minute=mid % 60)


class FrictionEngine:
    """Pattern detection over ExecutionLog → programmatic PlanProposal records."""

    LOOKBACK_DAYS = 14
    SHIFT_MIN_COUNT = 3
    FRICTION_MIN_COUNT = 3
    RADICAL_SHIFT_MINUTES = 120

    def analyze_friction_patterns(
        self,
        db: Session,
        user_id: int,
        *,
        as_of: date | None = None,
    ) -> list[PlanProposal]:
        """
        Scan the last 7–14 days of exception logs for the user and create proposals.

        `user_id` resolves against UserContext.user_id, else UserContext.id,
        else user_profile_id (single-tenant bridge until auth User exists).
        """
        ctx = self._resolve_context(db, user_id)
        if ctx is None:
            return []

        plans = self._plans_for_context(db, ctx)
        if not plans:
            return []

        plan_ids = [p.id for p in plans]
        items = (
            db.query(ExecutionItem)
            .filter(ExecutionItem.plan_id.in_(plan_ids), ExecutionItem.active.is_(True))
            .all()
        )
        if not items:
            return []

        item_by_id = {i.id: i for i in items}
        end = as_of or date.today()
        start = end - timedelta(days=self.LOOKBACK_DAYS)

        logs = (
            db.query(ExecutionLog)
            .filter(
                ExecutionLog.execution_item_id.in_(list(item_by_id.keys())),
                ExecutionLog.date >= start,
                ExecutionLog.date <= end,
            )
            .all()
        )

        by_item: dict[int, list[ExecutionLog]] = defaultdict(list)
        for log in logs:
            by_item[log.execution_item_id].append(log)

        created: list[PlanProposal] = []
        for item_id, item_logs in by_item.items():
            item = item_by_id[item_id]
            proposal = self._rule_schedule_shift(db, item, item_logs)
            if proposal is not None:
                created.append(proposal)
                continue
            proposal = self._rule_high_friction(db, item, item_logs)
            if proposal is not None:
                created.append(proposal)

        db.flush()
        return created

    def _resolve_context(self, db: Session, user_id: int) -> UserContext | None:
        ctx = db.query(UserContext).filter(UserContext.user_id == user_id).first()
        if ctx is not None:
            return ctx
        ctx = db.query(UserContext).filter(UserContext.id == user_id).first()
        if ctx is not None:
            return ctx
        return db.query(UserContext).filter(UserContext.user_profile_id == user_id).first()

    def _plans_for_context(self, db: Session, ctx: UserContext) -> list[Plan]:
        q = db.query(Plan)
        if ctx.user_profile_id is not None:
            linked = q.filter(Plan.user_profile_id == ctx.user_profile_id).all()
            if linked:
                return linked
        return q.order_by(Plan.id.asc()).all()

    def _existing_pending(self, db: Session, plan_id: int, execution_item_id: int, ptype: str) -> bool:
        for prop in execution_repo.list_proposals(db, plan_id):
            if prop.status != 'pending':
                continue
            payload = prop.payload or {}
            if payload.get('type') == ptype and payload.get('execution_item_id') == execution_item_id:
                return True
        return False

    def _rule_schedule_shift(
        self,
        db: Session,
        item: ExecutionItem,
        logs: list[ExecutionLog],
    ) -> PlanProposal | None:
        shifted = [log for log in logs if log.status == 'shifted_schedule']
        timed = [log for log in logs if log.logged_at_time is not None]

        preferred = _parse_preferred_time(item)
        radical = []
        if preferred is not None:
            for log in timed:
                delta = abs(_minutes(log.logged_at_time) - _minutes(preferred))
                if delta >= self.RADICAL_SHIFT_MINUTES:
                    radical.append(log)

        signal_count = max(len(shifted), len(radical))
        if signal_count < self.SHIFT_MIN_COUNT:
            return None
        if self._existing_pending(db, item.plan_id, item.id, 'reschedule'):
            return None

        sample_times = [log.logged_at_time for log in (radical or shifted) if log.logged_at_time]
        if not sample_times and timed:
            sample_times = [log.logged_at_time for log in timed if log.logged_at_time]
        suggested = _median_time(sample_times) if sample_times else time(12, 0)

        payload = {
            'type': 'reschedule',
            'execution_item_id': item.id,
            'suggested_time': suggested.isoformat(),
            'reason': 'Schedule drift detected from repeated shifted_schedule / off-plan times',
            'signal_count': signal_count,
            'window_days': self.LOOKBACK_DAYS,
        }
        return execution_repo.create_proposal(
            db,
            item.plan_id,
            status='pending',
            rationale=payload['reason'],
            payload=payload,
            created_by='friction_engine',
        )

    def _rule_high_friction(
        self,
        db: Session,
        item: ExecutionItem,
        logs: list[ExecutionLog],
    ) -> PlanProposal | None:
        hard = [log for log in logs if log.status in ('high_friction', 'skipped')]
        if len(hard) < self.FRICTION_MIN_COUNT:
            return None
        if self._existing_pending(db, item.plan_id, item.id, 'reduce_friction'):
            return None

        evening_hits = 0
        for log in hard:
            t = log.logged_at_time
            if t is not None and t.hour >= 18:
                evening_hits += 1

        suggested_time = '12:00:00' if evening_hits >= 2 else None
        payload: dict[str, Any] = {
            'type': 'reduce_friction',
            'execution_item_id': item.id,
            'title': item.title,
            'reason': (
                'High friction detected during evening hours'
                if evening_hits >= 2
                else f'Repeated high_friction/skipped logs for "{item.title}"'
            ),
            'signal_count': len(hard),
            'statuses': [log.status for log in hard],
            'window_days': self.LOOKBACK_DAYS,
            'suggested_actions': [
                {'action': 'replace', 'label': 'Show visual substitutes'},
                {'action': 'shorten', 'estimated_duration': 10},
            ],
        }
        if suggested_time:
            payload['suggested_time'] = suggested_time
            payload['type'] = 'reschedule'
            payload['reason'] = 'High friction detected during evening hours'

        if self._existing_pending(db, item.plan_id, item.id, payload['type']):
            return None

        return execution_repo.create_proposal(
            db,
            item.plan_id,
            status='pending',
            rationale=payload['reason'],
            payload=payload,
            created_by='friction_engine',
        )


friction_engine = FrictionEngine()
