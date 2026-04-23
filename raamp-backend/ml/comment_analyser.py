"""
ml/comment_analyser.py — Comment Spam + Sentiment Analyser
"""

import joblib, os, logging
from transformers import pipeline

logger = logging.getLogger(__name__)

SPAM_MODEL_PATH      = "ml/models/spam_classifier.pkl"
SPAM_VECTORIZER_PATH = "ml/models/spam_vectorizer.pkl"

_spam_model      = None
_spam_vectorizer = None
_sentiment_model = None
_loaded          = False


def _load_models():
    global _spam_model, _spam_vectorizer, _sentiment_model, _loaded
    if _loaded:
        return

    # Load spam classifier
    if os.path.exists(SPAM_MODEL_PATH):
        _spam_model      = joblib.load(SPAM_MODEL_PATH)
        _spam_vectorizer = joblib.load(SPAM_VECTORIZER_PATH)
        logger.info("✅ Spam classifier loaded")
    else:
        logger.warning("⚠️ Spam model not found — spam detection disabled")

    # Load sentiment model (downloads automatically on first run ~few seconds)
    try:
        _sentiment_model = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment"
        )
        logger.info("✅ Sentiment model loaded")
    except Exception as e:
        logger.error(f"❌ Sentiment model failed to load: {e}")

    _loaded = True


def analyse_comment(text: str) -> dict:
    """
    Analyse a single comment for spam and sentiment.
    Returns:
        {
            "is_spam": bool,
            "spam_confidence": float,
            "sentiment": "POSITIVE" | "NEUTRAL" | "NEGATIVE",
            "sentiment_score": float,
            "model_available": bool
        }
    """
    _load_models()

    result = {
        "is_spam": False,
        "spam_confidence": 0.0,
        "sentiment": "NEUTRAL",
        "sentiment_score": 0.0,
        "model_available": bool(_spam_model and _sentiment_model)
    }

    # Spam detection
    if _spam_model and _spam_vectorizer:
        X = _spam_vectorizer.transform([text])
        proba = _spam_model.predict_proba(X)[0]
        result["is_spam"]         = bool(proba[1] > 0.65)
        result["spam_confidence"] = round(float(proba[1]), 4)

    # Sentiment analysis
    if _sentiment_model:
        label_map = {
            "LABEL_0": "NEGATIVE",
            "LABEL_1": "NEUTRAL",
            "LABEL_2": "POSITIVE"
        }
        out = _sentiment_model(text[:512])[0]
        result["sentiment"]       = label_map.get(out["label"], "NEUTRAL")
        result["sentiment_score"] = round(out["score"], 4)

    return result