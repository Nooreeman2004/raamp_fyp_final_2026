"""
ml/model_trainer.py — RAAMP Caption ML Trainer
===============================================
Pulls caption_logs from MongoDB and trains two models:

  Model 1 — GradientBoostingRegressor
    Predicts engagement_rate from structural + linguistic caption features.
    Features: caption_length, word_count, VADER sentiment, punctuation signals,
              hashtag_count, emoji_count, has_cta, hour_posted, day_of_week,
              tone (label-encoded), asset_type (label-encoded).
    Target:   engagement_rate (float, stored on CaptionLogModel)

  Model 2 — TF-IDF + KMeans Clustering
    Groups captions into 8 style clusters. For each cluster, aggregates the
    top-N hashtags ranked by average engagement_rate. At inference time,
    a new caption is mapped to its nearest cluster and receives those hashtags.

Cold-start guard:
    Raises ColdStartError if < 50 labelled (engagement_rate is not None)
    documents exist. The ML router surfaces this as HTTP 400.

Artefacts saved to ml/models/:
    engagement_model.pkl    — fitted GradientBoostingRegressor pipeline
    cluster_model.pkl       — fitted TF-IDF vectorizer + KMeans
    cluster_hashtag_map.pkl — dict[cluster_id → list[hashtag]]
    label_encoders.pkl      — dict of LabelEncoders for categorical fields
    model_meta.json         — training metrics + timestamp + sample size
"""

import os
import re
import json
import math
import logging
import asyncio
import glob
from datetime import datetime, timezone
from typing import Any

import numpy as np
import joblib
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.metrics import mean_squared_error, mean_absolute_error, silhouette_score
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

from infrastructure.database.models.caption_log_model import CaptionLogModel

logger = logging.getLogger(__name__)

# ── paths ──────────────────────────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(_BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

ENGAGEMENT_MODEL_PATH  = os.path.join(MODELS_DIR, "engagement_model.pkl")
CLUSTER_MODEL_PATH     = os.path.join(MODELS_DIR, "cluster_model.pkl")
CLUSTER_HASHTAG_PATH   = os.path.join(MODELS_DIR, "cluster_hashtag_map.pkl")
LABEL_ENCODERS_PATH    = os.path.join(MODELS_DIR, "label_encoders.pkl")
MODEL_META_PATH        = os.path.join(MODELS_DIR, "model_meta.json")

# ── constants ──────────────────────────────────────────────────────────────────
MIN_SAMPLES   = 50        # cold-start threshold
N_CLUSTERS    = 8         # KMeans clusters
TOP_N_HASHTAGS = 10       # hashtags stored per cluster
CTA_KEYWORDS  = {"click", "link in bio", "shop", "buy", "dm", "order", "visit",
                 "grab", "get", "book", "sign up", "subscribe", "swipe"}

_vader = SentimentIntensityAnalyzer()

# ── optional Kaggle augmentation ───────────────────────────────────────────────
# This is intentionally optional so training still works offline / without Kaggle.
KAGGLE_DATASET_SLUG = os.getenv("KAGGLE_DATASET_SLUG", "rxsraghavagrawal/instagram-reach")
ENABLE_KAGGLE_TRAINING = os.getenv("ENABLE_KAGGLE_TRAINING", "0").strip() in {"1", "true", "True", "yes", "YES"}
KAGGLE_CSV_PATH = os.getenv("KAGGLE_CSV_PATH", "").strip()
TRAINING_SOURCE = os.getenv("TRAINING_SOURCE", "mongo").strip().lower()
"""
TRAINING_SOURCE controls where training data comes from:
  - "mongo"        : only CaptionLogModel from MongoDB (default)
  - "kaggle"       : only Kaggle rows (requires ENABLE_KAGGLE_TRAINING=1)
  - "mixed"        : combine Mongo + Kaggle (requires ENABLE_KAGGLE_TRAINING=1)
"""


def _safe_int(val: Any) -> int:
    try:
        if val is None:
            return 0
        if isinstance(val, str):
            val = val.replace(",", "").strip()
        return int(float(val))
    except Exception:
        return 0


def _load_kaggle_instagram_reach_rows() -> list[dict[str, Any]]:
    """
    Optionally load Kaggle dataset rows and convert them into training samples.

    Expected columns vary across dataset versions. We support a conservative subset:
      - caption:  Caption / caption / text
      - hashtags: Hashtags / hashtags
      - likes:    Likes / likes
      - comments: Comments / comments (optional, defaults to 0)
      - followers: Followers / followers (preferred for engagement proxy)
      - reach/impressions: Reach / Impressions (optional; if present, used as denominator)

    Engagement proxy:
      - If Reach exists and >0: (likes + comments) / reach
      - Else if Followers exists and >0: (likes + comments) / followers
    """
    if not ENABLE_KAGGLE_TRAINING:
        return []

    try:
        import kagglehub  # type: ignore
    except Exception as exc:
        logger.warning("⚠️  [ML Trainer] ENABLE_KAGGLE_TRAINING=1 but kagglehub not available: %s", exc)
        return []

    csv_path: str | None = None

    # Prefer a repo-local CSV if provided (stable path, avoids cache coupling).
    if KAGGLE_CSV_PATH and os.path.exists(KAGGLE_CSV_PATH):
        csv_path = KAGGLE_CSV_PATH
    else:
        try:
            dataset_path = kagglehub.dataset_download(KAGGLE_DATASET_SLUG)
        except Exception as exc:
            logger.warning("⚠️  [ML Trainer] Kaggle download failed for %s: %s", KAGGLE_DATASET_SLUG, exc)
            return []

        # Find the first CSV in the downloaded directory.
        csv_candidates = sorted(glob.glob(os.path.join(dataset_path, "*.csv")))
        if not csv_candidates:
            logger.warning("⚠️  [ML Trainer] Kaggle dataset downloaded but no CSV found at %s", dataset_path)
            return []
        csv_path = csv_candidates[0]
    rows: list[dict[str, Any]] = []

    import csv as _csv

    def _get(d: dict[str, Any], *keys: str) -> Any:
        for k in keys:
            if k in d and d[k] not in (None, ""):
                return d[k]
        return None

    with open(csv_path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        reader = _csv.DictReader(f)
        total_seen = 0
        dropped_bad_denom = 0
        dropped_bad_rate = 0
        for raw in reader:
            total_seen += 1
            caption = str(_get(raw, "Caption", "caption", "Text", "text") or "")
            hashtags_raw = str(_get(raw, "Hashtags", "hashtags") or "")
            likes = _safe_int(_get(raw, "Likes", "likes"))
            comments = _safe_int(_get(raw, "Comments", "comments"))
            followers = _safe_int(_get(raw, "Followers", "followers"))
            reach = _safe_int(_get(raw, "Reach", "reach"))
            impressions = _safe_int(_get(raw, "Impressions", "impressions"))

            denom = reach or impressions or followers
            if denom <= 0:
                dropped_bad_denom += 1
                continue

            engagement_rate = (likes + comments) / float(denom)
            # Drop impossible / broken rows (e.g., likes+comments > followers/reach/impressions).
            # This matches the common filter: (engagement_rate > 0) & (engagement_rate <= 1.0)
            if not (0.0 < engagement_rate <= 1.0):
                dropped_bad_rate += 1
                continue

            # Parse hashtags defensively (handles "#a #b" or "['a','b']" styles).
            hashtag_list = re.findall(r"#\\w+", hashtags_raw)
            hashtag_list = [h.lstrip("#").lower() for h in hashtag_list]

            rows.append(
                {
                    "caption_text": caption,
                    "tone": "Unknown",
                    "asset_type": "post",
                    "hour_posted": 12,   # neutral
                    "day_of_week": 2,    # neutral midweek
                    "hashtags": hashtag_list,
                    "engagement_rate": float(engagement_rate),
                }
            )

    logger.info(
        "📥 [ML Trainer] Kaggle rows: kept=%d dropped_bad_denom=%d dropped_bad_rate=%d total=%d | from %s",
        len(rows),
        dropped_bad_denom,
        dropped_bad_rate,
        total_seen,
        csv_path,
    )
    return rows


# ── custom exception ───────────────────────────────────────────────────────────
class ColdStartError(Exception):
    """Raised when there is insufficient labelled data to train a model."""


# ── feature engineering ────────────────────────────────────────────────────────
def _count_emojis(text: str) -> int:
    """Count emoji characters using Unicode range heuristic."""
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000027FF]+",
        flags=re.UNICODE,
    )
    return len(emoji_pattern.findall(text))


def _has_cta(text: str) -> int:
    """Return 1 if caption contains a call-to-action keyword, else 0."""
    lower = text.lower()
    return int(any(kw in lower for kw in CTA_KEYWORDS))


def extract_features(
    caption_text: str,
    tone: str,
    asset_type: str,
    hour_posted: int,
    day_of_week: int,
    tone_encoder: LabelEncoder,
    asset_type_encoder: LabelEncoder,
    hashtag_count: int | None = None,
) -> list[float]:
    """
    Convert a raw caption + metadata into a fixed-length numeric feature vector.

    Returns:
        list of floats matching the feature order used during training.
    """
    text = caption_text or ""
    words = text.split()
    sentiment = _vader.polarity_scores(text)

    # Safe label encoding — unknown categories fall back to 0
    try:
        tone_enc = int(tone_encoder.transform([tone])[0])
    except ValueError:
        tone_enc = 0
    try:
        asset_enc = int(asset_type_encoder.transform([asset_type])[0])
    except ValueError:
        asset_enc = 0

    # Note: hashtag_count is intentionally NOT used in the engagement regressor features.
    # On synthetic/bootstrapped labels it can dominate and collapse the model into a hashtag counter.
    # Hashtag intelligence is handled separately via the clustering + hashtag map.

    return [
        len(text),                        # caption_length
        len(words),                       # word_count
        float(sentiment["compound"]),     # vader_compound  (-1 → +1)
        float(sentiment["pos"]),          # vader_pos
        float(sentiment["neg"]),          # vader_neg
        text.count("!"),                  # exclamation_count
        text.count("?"),                  # question_count
        _count_emojis(text),              # emoji_count
        _has_cta(text),                   # has_cta
        int(hour_posted),                 # hour_posted  (0-23)
        int(day_of_week),                 # day_of_week  (0=Mon … 6=Sun)
        tone_enc,                         # tone  (label-encoded)
        asset_enc,                        # asset_type  (label-encoded)
    ]


FEATURE_NAMES = [
    "caption_length", "word_count", "vader_compound", "vader_pos", "vader_neg",
    "exclamation_count", "question_count", "emoji_count",
    "has_cta", "hour_posted", "day_of_week", "tone_encoded", "asset_type_encoded",
]


# ── main training function ─────────────────────────────────────────────────────
async def train_models() -> dict[str, Any]:
    """
    Pull caption_logs from MongoDB, engineer features, and train both models.

    Returns:
        dict with keys: r2, rmse, mae, inertia, silhouette, sample_size,
                        trained_at, model_version

    Raises:
        ColdStartError: if fewer than MIN_SAMPLES labelled documents exist.
    """
    logger.info("🤖 [ML Trainer] Starting training pipeline …")

    # ── 1. Load labelled data (Mongo, Kaggle, or both) ─────────────────────────
    docs: list[CaptionLogModel] = []
    kaggle_rows: list[dict[str, Any]] = []

    if TRAINING_SOURCE not in {"mongo", "kaggle", "mixed"}:
        logger.warning("⚠️  [ML Trainer] Unknown TRAINING_SOURCE=%s; falling back to 'mongo'", TRAINING_SOURCE)
        source = "mongo"
    else:
        source = TRAINING_SOURCE

    if source in {"mongo", "mixed"}:
        docs = await CaptionLogModel.find(
            CaptionLogModel.engagement_rate != None,  # noqa: E711
            CaptionLogModel.caption_text != None,
        ).to_list()

        # Filter to caption-type assets only (exclude hashtag/email/whatsapp sets)
        docs = [
            d for d in docs
            if d.asset_type and str(d.asset_type.value) in ("post", "story", "reel")
        ]

    if source in {"kaggle", "mixed"}:
        kaggle_rows = _load_kaggle_instagram_reach_rows()
        if source == "kaggle" and not kaggle_rows:
            raise ColdStartError(
                "TRAINING_SOURCE=kaggle but no Kaggle samples were loaded. "
                "Ensure ENABLE_KAGGLE_TRAINING=1, kagglehub is installed, and Kaggle credentials are configured."
            )

    sample_size = len(docs) + len(kaggle_rows)
    logger.info(
        "📊 [ML Trainer] Training source=%s | labelled samples: mongo=%d kaggle=%d total=%d",
        source,
        len(docs),
        len(kaggle_rows),
        sample_size,
    )

    if sample_size < MIN_SAMPLES:
        raise ColdStartError(
            f"Not enough labelled data to train: found {sample_size} documents "
            f"with engagement_rate set. Minimum required: {MIN_SAMPLES}. "
            "Post more content and wait for ROI metrics to be fetched."
        )

    # ── 2. Build label encoders ────────────────────────────────────────────────
    tones       = [d.tone or "General" for d in docs] + [r.get("tone") or "Unknown" for r in kaggle_rows]
    asset_types = [str(d.asset_type.value) if d.asset_type else "post" for d in docs] + [r.get("asset_type") or "post" for r in kaggle_rows]

    tone_enc       = LabelEncoder().fit(tones)
    asset_type_enc = LabelEncoder().fit(asset_types)

    # ── 3. Build feature matrix X and target y ─────────────────────────────────
    X_rows:  list[list[float]] = []
    y_vals:  list[float]       = []
    captions_for_clustering:   list[str]       = []
    hashtags_for_clustering:   list[list[str]] = []
    er_for_clustering:         list[float]     = []

    for doc in docs:
        text        = doc.caption_text or ""
        tone        = doc.tone or "General"
        asset_type  = str(doc.asset_type.value) if doc.asset_type else "post"
        created_at  = doc.created_at or datetime.now(timezone.utc)
        hour_posted = created_at.hour
        day_of_week = created_at.weekday()
        eng_rate    = float(doc.engagement_rate)
        hashtag_count = len(doc.hashtags or [])

        feats = extract_features(
            caption_text=text,
            tone=tone,
            asset_type=asset_type,
            hour_posted=hour_posted,
            day_of_week=day_of_week,
            tone_encoder=tone_enc,
            asset_type_encoder=asset_type_enc,
            hashtag_count=hashtag_count,
        )
        X_rows.append(feats)
        y_vals.append(eng_rate)

        captions_for_clustering.append(text)
        hashtags_for_clustering.append(doc.hashtags or [])
        er_for_clustering.append(eng_rate)

    # Append Kaggle samples (optional augmentation)
    for row in kaggle_rows:
        text = row.get("caption_text") or ""
        tone = row.get("tone") or "Unknown"
        asset_type = row.get("asset_type") or "post"
        hour_posted = int(row.get("hour_posted") or 12)
        day_of_week = int(row.get("day_of_week") or 2)
        eng_rate = float(row.get("engagement_rate") or 0.0)
        hashtags = row.get("hashtags") or []
        hashtag_count = len(hashtags)

        feats = extract_features(
            caption_text=text,
            tone=tone,
            asset_type=asset_type,
            hour_posted=hour_posted,
            day_of_week=day_of_week,
            tone_encoder=tone_enc,
            asset_type_encoder=asset_type_enc,
            hashtag_count=hashtag_count,
        )
        X_rows.append(feats)
        y_vals.append(eng_rate)
        captions_for_clustering.append(text)
        hashtags_for_clustering.append(hashtags)
        er_for_clustering.append(eng_rate)

    X = np.array(X_rows, dtype=float)
    y = np.array(y_vals, dtype=float)

    # ── 4. Train GradientBoostingRegressor ─────────────────────────────────────
    logger.info("🌲 [ML Trainer] Training GradientBoostingRegressor …")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    gbr = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        min_samples_split=5,
        random_state=42,
    )
    gbr.fit(X_train, y_train)

    y_pred = gbr.predict(X_test)
    ss_res = float(np.sum((y_test - y_pred) ** 2))
    ss_tot = float(np.sum((y_test - np.mean(y_test)) ** 2))
    r2   = round(1 - ss_res / ss_tot if ss_tot > 0 else 0.0, 4)
    rmse = round(float(math.sqrt(mean_squared_error(y_test, y_pred))), 6)
    mae  = round(float(mean_absolute_error(y_test, y_pred)), 6)
    logger.info("📈 [ML Trainer] GBR → R²=%.4f  RMSE=%.6f  MAE=%.6f", r2, rmse, mae)

    # ── 5. Train TF-IDF + KMeans ───────────────────────────────────────────────
    logger.info("🔤 [ML Trainer] Training TF-IDF + KMeans (n_clusters=%d) …", N_CLUSTERS)
    n_clusters_actual = min(N_CLUSTERS, sample_size)
    tfidf = TfidfVectorizer(
        max_features=500,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
    )
    tfidf_matrix = tfidf.fit_transform(captions_for_clustering)

    kmeans = KMeans(n_clusters=n_clusters_actual, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(tfidf_matrix)

    inertia = round(float(kmeans.inertia_), 2)
    sil_score = 0.0
    if n_clusters_actual > 1 and sample_size > n_clusters_actual:
        sil_score = round(float(silhouette_score(tfidf_matrix, cluster_labels, sample_size=min(sample_size, 500))), 4)
    logger.info("📊 [ML Trainer] KMeans → inertia=%.2f  silhouette=%.4f", inertia, sil_score)

    # ── 6. Build cluster → hashtag map ────────────────────────────────────────
    cluster_hashtag_acc: dict[int, dict[str, list[float]]] = {
        i: {} for i in range(n_clusters_actual)
    }
    for idx, cluster_id in enumerate(cluster_labels):
        er = er_for_clustering[idx]
        for tag in hashtags_for_clustering[idx]:
            tag = tag.strip().lower()
            if not tag:
                continue
            if tag not in cluster_hashtag_acc[cluster_id]:
                cluster_hashtag_acc[cluster_id][tag] = []
            cluster_hashtag_acc[cluster_id][tag].append(er)

    cluster_hashtag_map: dict[int, list[str]] = {}
    for cluster_id, tag_er_map in cluster_hashtag_acc.items():
        ranked = sorted(
            tag_er_map.items(),
            key=lambda kv: float(np.mean(kv[1])),
            reverse=True,
        )
        cluster_hashtag_map[cluster_id] = [tag for tag, _ in ranked[:TOP_N_HASHTAGS]]

    # ── 7. Persist all artefacts ───────────────────────────────────────────────
    joblib.dump(gbr,    ENGAGEMENT_MODEL_PATH)
    joblib.dump({"tfidf": tfidf, "kmeans": kmeans}, CLUSTER_MODEL_PATH)
    joblib.dump(cluster_hashtag_map, CLUSTER_HASHTAG_PATH)
    joblib.dump({"tone": tone_enc, "asset_type": asset_type_enc}, LABEL_ENCODERS_PATH)

    meta = {
        "trained_at":   datetime.now(timezone.utc).isoformat(),
        "model_version": "1.0.0",
        "sample_size":  sample_size,
        "r2":           r2,
        "rmse":         rmse,
        "mae":          mae,
        "inertia":      inertia,
        "silhouette":   sil_score,
        "n_clusters":   n_clusters_actual,
        "feature_names": FEATURE_NAMES,
    }
    with open(MODEL_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    logger.info("✅ [ML Trainer] All artefacts saved to %s", MODELS_DIR)
    return meta
