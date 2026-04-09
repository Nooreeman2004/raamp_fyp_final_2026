"""
Resolves social score, saturation, platform bias, and profit for content suggestions
when the primary source is TrendDetectionModel (spike record) rather than TrendSignal.

Preference order:
1) Completed TrendSignal whose keywords or search_interest data streams match the request keyword.
2) Metrics derived from detection fields + SocialTrendService (same helpers as the main pipeline,
   without launching Playwright saturation scrapes on this hot path).
"""
from __future__ import annotations

import logging
from typing import Dict, Tuple

from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from application.services.social_trend_service import SocialTrendService

logger = logging.getLogger(__name__)


def _norm_kw(s: str) -> str:
    return (s or "").strip().lower()


async def resolve_suggestion_metrics_from_detection(
    user_email: str,
    request_keyword: str,
    detection: TrendDetectionModel,
) -> Tuple[float, float, float, Dict[str, float]]:
    """
    Returns (profit_score, social_score, saturation_score, platform_bias).
    """
    kw = _norm_kw(request_keyword)

    signals = (
        await TrendSignalModel.find(
            TrendSignalModel.user_email == user_email,
            TrendSignalModel.fetch_status == "completed",
        )
        .sort(-TrendSignalModel.created_at)
        .limit(50)
        .to_list()
    )

    for s in signals:
        key_list = [_norm_kw(x) for x in (s.keywords or [])]
        if kw and kw in key_list:
            return _from_signal(s)

    for s in signals:
        data = (s.search_interest or {}).get("data") if isinstance(s.search_interest, dict) else None
        if isinstance(data, dict) and data and kw:
            for stream_key in data.keys():
                if _norm_kw(str(stream_key)) == kw:
                    return _from_signal(s)
                    break

    return _derive_from_detection(detection)


def _from_signal(s: TrendSignalModel) -> Tuple[float, float, float, Dict[str, float]]:
    return (
        float(s.profit_score if s.profit_score is not None else 50.0),
        float(s.social_score if s.social_score is not None else 50.0),
        float(s.saturation_score if s.saturation_score is not None else 50.0),
        dict(s.platform_bias or {}),
    )


def _derive_from_detection(detection: TrendDetectionModel) -> Tuple[float, float, float, Dict[str, float]]:
    """
    Derive metrics from spike statistics + semantic platform analysis (no Playwright).
    """
    social_service = SocialTrendService()
    platform_scores = social_service.analyze_platform_bias(detection.keyword)
    z = float(detection.z_score or 0.0)
    interest_growth = max(0.0, z * 10.0)
    social_score = social_service.compute_social_trend_score(interest_growth, platform_scores)

    # Saturation: high Google interest implies a "hot" topic (crowded attention);
    # market_gap is opportunity — higher gap → relatively lower saturation.
    cv = float(detection.current_value or 0.0)
    mg = float(detection.market_gap or 0.0)
    saturation_score = min(
        100.0,
        max(0.0, (cv * 0.75) + (15.0 * (1.0 - min(1.0, max(0.0, mg))))),
    )
    saturation_score = round(saturation_score, 2)

    if detection.profit_score is not None:
        profit_score = float(detection.profit_score)
    else:
        profit_score = min(100.0, max(0.0, z * 12.0 + mg * 40.0 + cv * 0.15))

    logger.info(
        "Suggestion metrics derived from detection keyword=%s: social=%.1f sat=%.1f profit=%.1f",
        detection.keyword,
        social_score,
        saturation_score,
        profit_score,
    )
    return (profit_score, social_score, saturation_score, platform_scores)
