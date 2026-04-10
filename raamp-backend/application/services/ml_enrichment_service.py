"""
application/services/ml_enrichment_service.py — Caption ML Enrichment Service
==============================================================================
This service is the bridge between the Gemini caption generation pipeline and
the ML layer. It is called AFTER Gemini returns 3 caption variants and BEFORE
the response is returned to the frontend.

What it does per variant:
  1. Calls caption_scorer.score_caption() → replaces hardcoded "Good" with
     a real ML-predicted engagement score + label.
  2. Calls hashtag_recommender.recommend_hashtags() → replaces Gemini's
     generated hashtags with cluster-ranked, engagement-optimised hashtags.
  3. Annotates each variant with `hashtag_source` to indicate ML enrichment.
  4. After scoring all 3 variants, sets `best_caption_id` to the index
     of the variant with the highest predicted_engagement_rate.

Graceful degradation:
  - If any model file is missing (not yet trained), variants are returned
    unchanged. The caption pipeline is never interrupted by ML failures.
  - All ML calls are wrapped in try/except with logged warnings.
  - caption_scorer and hashtag_recommender handle their own cold-start stubs.

Threading note:
  caption_scorer.score_caption() is synchronous (< 5 ms). We run it in an
  asyncio executor so as not to block the event loop, consistent with the
  project's async-first pattern.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

logger = logging.getLogger(__name__)


async def enrich_captions(
    variants: list[dict],
    tone: str = "General",
    asset_type: str = "post",
    hour_posted: Optional[int] = None,
    day_of_week: Optional[int] = None,
) -> tuple[list[dict], int]:
    """
    Enrich Gemini-generated caption variants with ML scoring and hashtag
    recommendations.

    Args:
        variants:     List of caption variant dicts from content_generation_service.
                      Each dict is expected to have keys: id, caption, tone, hashtags,
                      predicted_performance.
        tone:         The overall campaign tone (passed to caption scorer).
        asset_type:   Platform type: "post", "story", or "reel".
        hour_posted:  Hour of day context for scoring (0–23). Defaults to current hour.
        day_of_week:  Day of week context (0=Mon … 6=Sun). Defaults to current day.

    Returns:
        Tuple of:
          - enriched variants list (same structure, fields updated)
          - best_caption_id: int index (1-based) of highest-scoring variant
    """
    if not variants:
        return variants, 1

    # Default temporal context to current time if not provided
    now = datetime.now(timezone.utc)
    hour_posted  = hour_posted  if hour_posted  is not None else now.hour
    day_of_week  = day_of_week  if day_of_week  is not None else now.weekday()

    # Lazy imports — keeps startup fast when models are not yet trained
    try:
        from ml.caption_scorer      import score_caption
        from ml.hashtag_recommender import recommend_hashtags, get_cluster_id
    except ImportError as exc:
        logger.warning("⚠️  [MLEnrichment] ML modules not importable: %s — skipping enrichment", exc)
        return variants, 1

    enriched      = []
    best_idx      = 0
    best_eng_rate = -1.0

    for i, variant in enumerate(variants):
        caption_text = variant.get("caption", "")
        variant_tone = variant.get("tone", tone)

        # ── Score the caption ──────────────────────────────────────────────────
        try:
            score_result = await asyncio.to_thread(
                score_caption,
                caption_text,
                variant_tone,
                asset_type,
                hour_posted,
                day_of_week,
            )
        except Exception as exc:
            logger.warning("⚠️  [MLEnrichment] Scoring failed for variant %d: %s", i + 1, exc)
            score_result = {
                "engagement_rate":     0.03,
                "score_label":         "Moderate",
                "confidence":          "Low",
                "feature_importances": {},
                "model_available":     False,
            }

        # ── Recommend hashtags ────────────────────────────────────────────────
        try:
            ml_hashtags = await asyncio.to_thread(recommend_hashtags, caption_text)
            cluster_id  = await asyncio.to_thread(get_cluster_id,     caption_text)
        except Exception as exc:
            logger.warning("⚠️  [MLEnrichment] Hashtag recommendation failed for variant %d: %s", i + 1, exc)
            ml_hashtags = []
            cluster_id  = None

        # ── Build enriched variant ────────────────────────────────────────────
        updated = dict(variant)  # shallow copy — never mutate caller's dict

        # Replace predicted_performance with real ML score dict
        updated["predicted_performance"] = score_result["score_label"]    # keep label for backward compat
        updated["ml_score"] = {
            "engagement_rate":     score_result["engagement_rate"],
            "score_label":         score_result["score_label"],
            "confidence":          score_result["confidence"],
            "feature_importances": score_result["feature_importances"],
            "model_available":     score_result["model_available"],
        }

        # Keep Gemini hashtags as the default (business-specific).
        # Attach ML hashtags separately so the frontend can optionally display them
        # without overriding domain relevance.
        updated["ml_hashtags"] = ml_hashtags
        updated["hashtag_source"] = (
            "gemini_generated"
            if not ml_hashtags
            else (f"ml_cluster_{cluster_id}" if cluster_id is not None else "ml_cluster_unknown")
        )

        # Track best variant
        eng = score_result["engagement_rate"]
        if eng > best_eng_rate:
            best_eng_rate = eng
            best_idx      = i

        enriched.append(updated)
        logger.debug(
            "[MLEnrichment] Variant %d → score=%.4f (%s) | hashtag_source=%s",
            i + 1, eng, score_result["score_label"], updated["hashtag_source"],
        )

    best_caption_id = enriched[best_idx].get("id", best_idx + 1)
    logger.info(
        "✅ [MLEnrichment] Enriched %d variants. Best: variant %s (rate=%.4f)",
        len(enriched), best_caption_id, best_eng_rate,
    )
    return enriched, best_caption_id
