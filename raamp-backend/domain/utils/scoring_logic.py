"""
Scoring Interpretation Logic
============================
Central source of truth for interpreting marketing analysis scores.
Used by both backend logic and provided to frontend via API.
"""

from enum import Enum
from typing import Dict, Any

class RelevanceLevel(str, Enum):
    RELEVANT = "relevant"
    WEAK = "weak"
    NOT_RELEVANT = "not_relevant"

class ScoreGrade(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    POOR = "poor"

# Thresholds
THRESHOLDS = {
    "relevance": {
        "good": 7.0,
        "weak": 4.0
    },
    "composite": {
        "excellent": 8.0,
        "good": 6.0
    }
}

def get_relevance_level(score: float) -> RelevanceLevel:
    """Interpret restaurant relevance score"""
    if score >= THRESHOLDS["relevance"]["good"]:
        return RelevanceLevel.RELEVANT
    if score >= THRESHOLDS["relevance"]["weak"]:
        return RelevanceLevel.WEAK
    return RelevanceLevel.NOT_RELEVANT

def get_score_grade(score: float) -> ScoreGrade:
    """Interpret composite/viral/aesthetic score"""
    if score >= THRESHOLDS["composite"]["excellent"]:
        return ScoreGrade.EXCELLENT
    if score >= THRESHOLDS["composite"]["good"]:
        return ScoreGrade.GOOD
    return ScoreGrade.POOR

def get_scoring_config() -> Dict[str, Any]:
    """Returns the full scoring configuration for frontend consumption"""
    return {
        "thresholds": THRESHOLDS,
        "levels": {
            "relevance": [l.value for l in RelevanceLevel],
            "grade": [g.value for g in ScoreGrade]
        }
    }

def generate_test_advice(score_gap: float) -> str:
    """Generate human-readable advice based on the gap between top two images"""
    if score_gap < 0.5:
        return "⚠️ Very close scores - A/B test strongly recommended to find the winner!"
    elif score_gap < 1.5:
        return f"📊 Moderate gap ({score_gap:.2f}) - A/B test to confirm the leader"
    else:
        return f"✅ Clear leader (gap: {score_gap:.2f}) - but test to verify real-world performance"

def is_irrelevant(score: float) -> bool:
    """Check if image is irrelevant for marketing"""
    return score < THRESHOLDS["relevance"]["weak"]
