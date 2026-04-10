"""
ml/caption_scorer.py — Real-time Caption Engagement Scorer
===========================================================
Loads the trained GradientBoostingRegressor from disk at import time and
exposes a single synchronous function `score_caption()` that the enrichment
service calls for each caption variant in the pipeline.

Scoring is intentionally synchronous (< 5 ms per caption) so it does not
require async overhead. The enrichment service wraps calls in asyncio.to_thread
if needed.

Score label thresholds (based on typical Instagram engagement benchmarks):
    < 0.02  → "Weak"       (below 2% engagement rate)
    0.02–0.05 → "Moderate" (2–5%, average range)
    > 0.05  → "Strong"     (above 5%, above average)

Graceful degradation:
    If the model file is missing (not yet trained), score_caption() returns
    a neutral stub dict so the caption pipeline never crashes.
"""

import os
import logging
from typing import Optional

import numpy as np
import joblib

from ml.model_trainer import (
    ENGAGEMENT_MODEL_PATH,
    LABEL_ENCODERS_PATH,
    FEATURE_NAMES,
    extract_features,
)

logger = logging.getLogger(__name__)

# ── model state (module-level singletons, loaded once) ─────────────────────────
_gbr_model       = None
_label_encoders  = None
_model_loaded    = False


def _load_model() -> bool:
    """
    Attempt to load the GBR model and label encoders from disk.
    Called lazily on first score_caption() call.
    Returns True if loaded successfully, False otherwise.
    """
    global _gbr_model, _label_encoders, _model_loaded
    if _model_loaded:
        return _gbr_model is not None

    if not os.path.exists(ENGAGEMENT_MODEL_PATH):
        logger.warning("⚠️  [CaptionScorer] Model not found at %s — cold start mode", ENGAGEMENT_MODEL_PATH)
        _model_loaded = True
        return False

    if not os.path.exists(LABEL_ENCODERS_PATH):
        logger.warning("⚠️  [CaptionScorer] Label encoders not found — cold start mode")
        _model_loaded = True
        return False

    try:
        _gbr_model      = joblib.load(ENGAGEMENT_MODEL_PATH)
        _label_encoders = joblib.load(LABEL_ENCODERS_PATH)
        _model_loaded   = True
        logger.info("✅ [CaptionScorer] GBR model loaded successfully")
        return True
    except Exception as exc:
        logger.error("❌ [CaptionScorer] Failed to load model: %s", exc)
        _model_loaded = True
        return False


def reload_model() -> bool:
    """
    Force re-load the model from disk (called after retraining).
    Resets the module-level singleton so next call picks up the new .pkl.
    """
    global _model_loaded
    _model_loaded = False
    return _load_model()


def _score_label(predicted_rate: float) -> str:
    """Map predicted engagement_rate to a human-readable label."""
    if predicted_rate < 0.02:
        return "Weak"
    if predicted_rate <= 0.05:
        return "Moderate"
    return "Strong"


def _confidence_label(predicted_rate: float) -> str:
    """
    Derive a confidence string based on prediction magnitude.
    Higher predicted rates tend to be harder to achieve, signalling lower confidence.
    """
    if predicted_rate < 0.01:
        return "High"       # model is confident this won't perform well
    if predicted_rate < 0.04:
        return "Medium"
    return "Low"            # very high engagement is harder to guarantee


def score_caption(
    caption_text: str,
    tone: str = "General",
    asset_type: str = "post",
    hour_posted: int = 12,
    day_of_week: int = 1,
) -> dict:
    """
    Score a caption variant using the trained GradientBoostingRegressor.

    Args:
        caption_text:  The raw caption string to score.
        tone:          Tone label (e.g. "Vibrant", "Professional").
        asset_type:    Content type: "post", "story", or "reel".
        hour_posted:   Hour of day to simulate posting (0–23, default noon).
        day_of_week:   Day of week (0=Monday … 6=Sunday, default Tuesday).

    Returns:
        {
            "engagement_rate":     float,   # predicted rate (e.g. 0.034 = 3.4%)
            "score_label":         str,     # "Weak" | "Moderate" | "Strong"
            "confidence":          str,     # "High" | "Medium" | "Low"
            "feature_importances": dict,    # top-5 feature → importance score
            "model_available":     bool,    # False means cold-start stub
        }
    """
    if not _load_model():
        # Cold-start stub — neutral, does not expose error to caption pipeline
        return {
            "engagement_rate":     0.03,
            "score_label":         "Moderate",
            "confidence":          "Low",
            "feature_importances": {},
            "model_available":     False,
        }

    try:
        feats = extract_features(
            caption_text=caption_text,
            tone=tone,
            asset_type=asset_type,
            hour_posted=hour_posted,
            day_of_week=day_of_week,
            tone_encoder=_label_encoders["tone"],
            asset_type_encoder=_label_encoders["asset_type"],
            hashtag_count=None,
        )
        X = np.array([feats], dtype=float)
        predicted_rate = float(np.clip(_gbr_model.predict(X)[0], 0.0, 1.0))

        # Feature importances — top 5 by weight
        importances = _gbr_model.feature_importances_
        ranked = sorted(
            zip(FEATURE_NAMES, importances),
            key=lambda kv: kv[1],
            reverse=True,
        )
        top5_importances = {name: round(float(imp), 4) for name, imp in ranked[:5]}

        return {
            "engagement_rate":     round(predicted_rate, 4),
            "score_label":         _score_label(predicted_rate),
            "confidence":          _confidence_label(predicted_rate),
            "feature_importances": top5_importances,
            "model_available":     True,
        }

    except Exception as exc:
        logger.error("❌ [CaptionScorer] Scoring failed: %s", exc)
        # Graceful degradation — never raise into the caption pipeline
        return {
            "engagement_rate":     0.03,
            "score_label":         "Moderate",
            "confidence":          "Low",
            "feature_importances": {},
            "model_available":     False,
        }
