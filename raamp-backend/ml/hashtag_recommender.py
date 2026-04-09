"""
ml/hashtag_recommender.py — Cluster-based Hashtag Recommender
=============================================================
Loads the trained TF-IDF vectorizer + KMeans model at import time and
maps any new caption text to its nearest content cluster, then returns
the pre-computed top-N hashtags for that cluster.

Approach:
    1. Vectorize caption_text using the fitted TF-IDF vocabulary.
    2. Identify the nearest KMeans cluster centroid.
    3. Return the stored list of top hashtags for that cluster.
       (The list was built during training by ranking hashtags within each
       cluster by mean engagement_rate of associated posts.)

Graceful degradation:
    If one or more model files are missing, recommend_hashtags() returns []
    without raising — the caption pipeline substitutes Gemini's original hashtags.
"""

import os
import logging
from typing import Optional

import joblib

from ml.model_trainer import (
    CLUSTER_MODEL_PATH,
    CLUSTER_HASHTAG_PATH,
    TOP_N_HASHTAGS,
)

logger = logging.getLogger(__name__)

# ── module-level singletons ────────────────────────────────────────────────────
_cluster_model       = None   # dict: {"tfidf": TfidfVectorizer, "kmeans": KMeans}
_cluster_hashtag_map = None   # dict: {cluster_id: [hashtag, ...]}
_model_loaded        = False


def _load_models() -> bool:
    """
    Attempt to load TF-IDF + KMeans and the cluster→hashtag map from disk.
    Returns True if both artefacts are available.
    """
    global _cluster_model, _cluster_hashtag_map, _model_loaded
    if _model_loaded:
        return _cluster_model is not None

    if not os.path.exists(CLUSTER_MODEL_PATH) or not os.path.exists(CLUSTER_HASHTAG_PATH):
        logger.warning(
            "⚠️  [HashtagRecommender] Cluster model or hashtag map not found — "
            "hashtag recommendation disabled until training is run."
        )
        _model_loaded = True
        return False

    try:
        _cluster_model       = joblib.load(CLUSTER_MODEL_PATH)
        _cluster_hashtag_map = joblib.load(CLUSTER_HASHTAG_PATH)
        _model_loaded        = True
        logger.info(
            "✅ [HashtagRecommender] Cluster model loaded — %d clusters available",
            len(_cluster_hashtag_map),
        )
        return True
    except Exception as exc:
        logger.error("❌ [HashtagRecommender] Failed to load cluster models: %s", exc)
        _model_loaded = True
        return False


def reload_models() -> bool:
    """Force re-load from disk (called after retraining)."""
    global _model_loaded
    _model_loaded = False
    return _load_models()


def recommend_hashtags(caption_text: str, top_n: int = TOP_N_HASHTAGS) -> list[str]:
    """
    Return the top-N engagement-ranked hashtags for the cluster most similar
    to caption_text.

    Args:
        caption_text: The caption to find hashtags for.
        top_n:        Maximum number of hashtags to return (default 10).

    Returns:
        List of hashtag strings (may be empty if model is not yet trained).
        Hashtags are returned without deduplication guarantee — caller should
        deduplicate against the caption's existing inline hashtags if needed.
    """
    if not _load_models():
        return []

    try:
        tfidf  = _cluster_model["tfidf"]
        kmeans = _cluster_model["kmeans"]

        vec     = tfidf.transform([caption_text or ""])
        cluster = int(kmeans.predict(vec)[0])
        hashtags = _cluster_hashtag_map.get(cluster, [])

        logger.debug(
            "[HashtagRecommender] caption -> cluster %d -> %d hashtags",
            cluster, len(hashtags),
        )
        return hashtags[:top_n]

    except Exception as exc:
        logger.error("❌ [HashtagRecommender] Recommendation failed: %s", exc)
        return []


def get_cluster_id(caption_text: str) -> Optional[int]:
    """
    Return the cluster ID for a caption (used for the hashtag_source field).
    Returns None if model is unavailable.
    """
    if not _load_models():
        return None
    try:
        tfidf  = _cluster_model["tfidf"]
        kmeans = _cluster_model["kmeans"]
        vec    = tfidf.transform([caption_text or ""])
        return int(kmeans.predict(vec)[0])
    except Exception:
        return None
