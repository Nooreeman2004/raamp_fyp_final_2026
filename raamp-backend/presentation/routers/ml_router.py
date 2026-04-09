"""
presentation/routers/ml_router.py — RAAMP ML API Router
=========================================================
Exposes two endpoints under /api/ml:

  POST /api/ml/train
    Triggers model training from caption_logs data.
    Returns training metrics (R², RMSE, MAE, silhouette score).
    Returns HTTP 400 if insufficient data (ColdStartError).
    After training, hot-swaps the in-memory model so subsequent
    score_caption() calls use the new weights immediately.

  GET /api/ml/model-stats
    Reads model_meta.json (written by the trainer) and returns the
    last training run's metrics + timestamp + sample size.
    Returns HTTP 404 if model has never been trained.

Both endpoints are authenticated via the existing get_current_user_email
dependency to prevent public access to training controls.
"""

import json
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from presentation.routers.auth_router import get_current_user_email
from ml.model_trainer import MODEL_META_PATH, ColdStartError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml", tags=["ML — Caption Intelligence"])


@router.post("/train", summary="Train caption ML models from MongoDB data")
async def train_models_endpoint(
    current_user: str = Depends(get_current_user_email),
):
    """
    Trigger a full model training run:
      1. Pull caption_logs with engagement_rate populated
      2. Train GradientBoostingRegressor for engagement prediction
      3. Train TF-IDF + KMeans for hashtag clustering
      4. Persist .pkl artefacts + model_meta.json
      5. Hot-reload in-memory model instances

    Returns training metrics on success.
    Returns HTTP 400 with explanation if < 50 labelled documents exist.
    """
    from ml.model_trainer import train_models

    logger.info("🚀 [ML Router] Training triggered by user: %s", current_user)
    try:
        metrics = await train_models()
    except ColdStartError as cse:
        logger.warning("❄️  [ML Router] ColdStartError: %s", cse)
        raise HTTPException(status_code=400, detail=str(cse))
    except Exception as exc:
        logger.error("❌ [ML Router] Training failed unexpectedly: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Training failed: {str(exc)}")

    # Hot-reload both ML modules so they pick up the new .pkl without restart
    try:
        from ml.caption_scorer      import reload_model   as reload_scorer
        from ml.hashtag_recommender import reload_models  as reload_recommender
        reload_scorer()
        reload_recommender()
        logger.info("✅ [ML Router] In-memory models hot-reloaded after training")
    except Exception as exc:
        logger.warning("⚠️  [ML Router] Hot-reload partially failed: %s", exc)

    return {
        "success":       True,
        "message":       "Models trained and loaded successfully.",
        "trained_at":    metrics["trained_at"],
        "model_version": metrics["model_version"],
        "sample_size":   metrics["sample_size"],
        "regression": {
            "r2":   metrics["r2"],
            "rmse": metrics["rmse"],
            "mae":  metrics["mae"],
        },
        "clustering": {
            "n_clusters":  metrics["n_clusters"],
            "inertia":     metrics["inertia"],
            "silhouette":  metrics["silhouette"],
        },
    }


@router.get("/model-stats", summary="Get last training run metrics")
async def get_model_stats(
    current_user: str = Depends(get_current_user_email),
):
    """
    Return the metadata from the most recent training run, including:
      - trained_at timestamp
      - sample_size (number of training documents)
      - regression metrics: R², RMSE, MAE
      - clustering metrics: inertia, silhouette score, n_clusters
      - feature_names used during training
      - model_version

    Returns HTTP 404 if no training has been run yet.
    """
    if not os.path.exists(MODEL_META_PATH):
        raise HTTPException(
            status_code=404,
            detail=(
                "No trained model found. "
                "Call POST /api/ml/train first to train the models."
            ),
        )

    try:
        with open(MODEL_META_PATH, "r") as f:
            meta = json.load(f)
    except Exception as exc:
        logger.error("❌ [ML Router] Failed to read model_meta.json: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to read model metadata.")

    # Annotate with model availability flag
    meta["model_files_present"] = {
        "engagement_model": os.path.exists(
            os.path.join(os.path.dirname(MODEL_META_PATH), "engagement_model.pkl")
        ),
        "cluster_model": os.path.exists(
            os.path.join(os.path.dirname(MODEL_META_PATH), "cluster_model.pkl")
        ),
        "cluster_hashtag_map": os.path.exists(
            os.path.join(os.path.dirname(MODEL_META_PATH), "cluster_hashtag_map.pkl")
        ),
    }

    return meta
