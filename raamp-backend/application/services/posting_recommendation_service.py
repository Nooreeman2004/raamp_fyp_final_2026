import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    # Python 3.9+
    from zoneinfo import ZoneInfo  # type: ignore
except Exception:  # pragma: no cover
    ZoneInfo = None  # type: ignore

from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.instagram_post_model import InstagramPostModel

logger = logging.getLogger(__name__)


HOUR_BUCKETS: List[Tuple[int, int]] = [
    (9, 12),
    (12, 15),
    (15, 18),
    (18, 21),
    (21, 24),
]

# Keep recommendations stable + explainable. We output 2-hour windows even though
# scoring buckets are 3 hours, to avoid overly broad "post anytime in 3 hours".
BUCKET_TO_SLOT: Dict[Tuple[int, int], Tuple[str, str]] = {
    (9, 12): ("09:00", "11:00"),
    (12, 15): ("12:00", "14:00"),
    (15, 18): ("15:00", "17:00"),
    (18, 21): ("19:00", "21:00"),
    (21, 24): ("21:00", "23:00"),
}

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


@dataclass(frozen=True)
class PostingRecommendationResult:
    timezone: str
    next_best_time: str
    days: List[str]
    slots: List[Dict[str, str]]
    confidence: str  # "high" | "low"


class PostingRecommendationService:
    """
    Minimal but scalable posting recommendation engine.

    Layer 1 (personalized): uses user's recent post performance stored in DB.
    Layer 2 (fallback): deterministic heuristic based on business_type + region.
    """

    DEFAULT_TZ = "Asia/Karachi"

    async def get_recommendations(self, user_id: str) -> PostingRecommendationResult:
        tz = await self._resolve_timezone(user_id)

        # Layer 1: Personalized (only if we have enough data)
        personalized = await self._recommend_from_recent_posts(user_id=user_id, tz=tz)
        if personalized is not None:
            return personalized

        # Layer 2: Fallback heuristic (safe default)
        return await self._fallback_heuristic(user_id=user_id, tz=tz)

    async def _resolve_timezone(self, user_id: str) -> str:
        """
        Resolve a best-effort timezone.
        Today: we don't store timezone explicitly, so infer from country/location.
        """
        try:
            biz = await BusinessModel.find_one({"user_id": user_id})
        except Exception:
            biz = None

        country = (getattr(biz, "country", None) or "").strip().lower()
        location = (getattr(biz, "city", None) or "").strip().lower()
        # Pakistan default as requested.
        if "pakistan" in country or country in {"pk", "pak"}:
            return "Asia/Karachi"
        # Heuristic for common cases; otherwise default to Asia/Karachi (product baseline).
        if any(x in location for x in ["karachi", "lahore", "islamabad"]):
            return "Asia/Karachi"

        return self.DEFAULT_TZ

    def _to_local(self, dt: datetime, tz: str) -> datetime:
        if not isinstance(dt, datetime):
            return datetime.utcnow()
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=ZoneInfo("UTC") if ZoneInfo else None)
        if ZoneInfo:
            try:
                return dt.astimezone(ZoneInfo(tz))
            except Exception:
                return dt
        return dt

    def _hour_bucket(self, hour: int) -> Optional[Tuple[int, int]]:
        for start, end in HOUR_BUCKETS:
            if start <= hour < end:
                return (start, end)
        return None

    def _engagement_rate(self, post: InstagramPostModel) -> float:
        """
        Best-effort engagement rate:
        - Prefer stored roi_metrics.engagement_rate if non-zero.
        - Else compute simple engagement / reach proxy.
        """
        try:
            rm = getattr(post, "roi_metrics", None)
            if rm is not None:
                er = float(getattr(rm, "engagement_rate", 0.0) or 0.0)
                if er > 0:
                    return er

                likes = float(getattr(rm, "likes", 0) or 0)
                comments = float(getattr(rm, "comments", 0) or 0)
                shares = float(getattr(rm, "shares", 0) or 0)
                saved = float(getattr(rm, "saved", 0) or 0)
                engagement = likes + comments + shares + saved

                reach = float(getattr(rm, "reach", 0) or 0)
                impressions = float(getattr(rm, "impressions", 0) or 0)
                denom = max(1.0, reach, impressions)
                return float(engagement / denom)
        except Exception:
            return 0.0
        return 0.0

    def _recency_weight(self, post_time_utc: datetime, now_utc: datetime) -> float:
        """
        Exponential decay; half-life ~14 days.
        """
        try:
            age_days = max(0.0, (now_utc - post_time_utc).total_seconds() / 86400.0)
        except Exception:
            age_days = 999.0
        half_life = 14.0
        # weight = 0.5^(age/half_life)
        return float(2 ** (-age_days / half_life))

    async def _recommend_from_recent_posts(self, *, user_id: str, tz: str) -> Optional[PostingRecommendationResult]:
        """
        Personalized scoring from recent post performance.
        Returns None if insufficient data.
        """
        now_utc = datetime.utcnow()
        window_start = now_utc - timedelta(days=30)

        # Pull a bounded number of recent posts to keep it fast.
        posts = (
            await InstagramPostModel.find(
                InstagramPostModel.user_id == user_id.lower().strip(),
                InstagramPostModel.created_at >= window_start,
            )
            .sort(-InstagramPostModel.created_at)
            .limit(60)
            .to_list()
        )

        # Use only posts that have any meaningful ROI metrics.
        scored_rows: List[Tuple[str, Tuple[int, int], float]] = []
        for p in posts:
            created_at = getattr(p, "published_at", None) or getattr(p, "created_at", None)
            if not isinstance(created_at, datetime):
                continue

            er = self._engagement_rate(p)
            if er <= 0:
                continue

            local_dt = self._to_local(created_at, tz)
            bucket = self._hour_bucket(int(local_dt.hour))
            if bucket is None:
                continue

            weekday = WEEKDAYS[int(local_dt.weekday())]
            w = self._recency_weight(created_at if created_at.tzinfo is None else created_at.astimezone(ZoneInfo("UTC") if ZoneInfo else created_at.tzinfo), now_utc)
            score = float(er) * 100.0 * float(w)
            scored_rows.append((weekday, bucket, score))

        # Guardrail: avoid overfitting tiny data.
        if len(scored_rows) < 8:
            return None

        # Aggregate per weekday + bucket
        slot_scores: Dict[Tuple[str, Tuple[int, int]], float] = {}
        day_scores: Dict[str, float] = {}
        for weekday, bucket, score in scored_rows:
            slot_scores[(weekday, bucket)] = float(slot_scores.get((weekday, bucket), 0.0) + score)
            day_scores[weekday] = float(day_scores.get(weekday, 0.0) + score)

        best_days = [d for d, _ in sorted(day_scores.items(), key=lambda kv: kv[1], reverse=True)[:3]]
        best_slots = sorted(slot_scores.items(), key=lambda kv: kv[1], reverse=True)

        # Pick up to 3 unique buckets, preferring those on best days.
        picked: List[Tuple[int, int]] = []
        for (weekday, bucket), _score in best_slots:
            if weekday not in best_days:
                continue
            if bucket not in picked:
                picked.append(bucket)
            if len(picked) >= 3:
                break
        # If still empty, backfill from any day
        if not picked:
            for (_weekday, bucket), _score in best_slots:
                if bucket not in picked:
                    picked.append(bucket)
                if len(picked) >= 2:
                    break

        slots = []
        for b in picked:
            start, end = BUCKET_TO_SLOT.get(b, ("12:00", "14:00"))
            slots.append({"start": start, "end": end})

        next_best_time = self._compute_next_best_time(now_local=self._to_local(now_utc, tz), days=best_days, slots=slots)

        return PostingRecommendationResult(
            timezone=tz,
            next_best_time=next_best_time,
            days=best_days,
            slots=slots,
            confidence="high",
        )

    def _compute_next_best_time(self, *, now_local: datetime, days: List[str], slots: List[Dict[str, str]]) -> str:
        """
        Compute next occurrence of the best day + first slot start time.
        Returns ISO string WITHOUT timezone offset to match frontend expectations.
        """
        if not days or not slots:
            # fallback to next day 19:00
            dt = (now_local + timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)
            return dt.replace(tzinfo=None).isoformat()

        # Choose first day and first slot.
        day_name = days[0]
        slot_start = (slots[0].get("start") or "19:00").strip()
        try:
            hh, mm = [int(x) for x in slot_start.split(":")]
        except Exception:
            hh, mm = 19, 0

        target_weekday = WEEKDAYS.index(day_name) if day_name in WEEKDAYS else int(now_local.weekday())
        days_ahead = (target_weekday - int(now_local.weekday())) % 7
        candidate = now_local.replace(hour=hh, minute=mm, second=0, microsecond=0) + timedelta(days=days_ahead)
        if candidate <= now_local:
            candidate = candidate + timedelta(days=7)
        return candidate.replace(tzinfo=None).isoformat()

    async def _fallback_heuristic(self, *, user_id: str, tz: str) -> PostingRecommendationResult:
        """
        Deterministic fallback that is honest (low confidence) and region-aware.
        """
        try:
            biz = await BusinessModel.find_one({"user_id": user_id})
        except Exception:
            biz = None

        business_type = (getattr(biz, "business_type", None) or "").strip().lower()
        country = (getattr(biz, "country", None) or "").strip().lower()

        # Base default (Pakistan default as requested)
        days = ["Tuesday", "Thursday", "Saturday"]
        slots = [{"start": "12:00", "end": "14:00"}, {"start": "19:00", "end": "21:00"}]

        # Lightweight niche refinement (safe; easy to expand later)
        if any(k in business_type for k in ["fashion", "clothing", "boutique"]):
            slots = [{"start": "19:00", "end": "21:00"}, {"start": "21:00", "end": "23:00"}]
        elif any(k in business_type for k in ["food", "restaurant", "cafe", "bakery"]):
            slots = [{"start": "12:00", "end": "14:00"}, {"start": "19:00", "end": "21:00"}]
        elif any(k in business_type for k in ["tech", "software", "saas"]):
            days = ["Monday", "Wednesday", "Friday"]
            slots = [{"start": "15:00", "end": "17:00"}, {"start": "12:00", "end": "14:00"}]

        # Region tweak: if clearly not Pakistan, keep same but set timezone default already resolved.
        if country and "pakistan" not in country:
            # Keep stable defaults unless we have a dedicated mapping.
            pass

        next_best_time = self._compute_next_best_time(now_local=self._to_local(datetime.utcnow(), tz), days=days, slots=slots)

        return PostingRecommendationResult(
            timezone=tz,
            next_best_time=next_best_time,
            days=days,
            slots=slots,
            confidence="low",
        )

