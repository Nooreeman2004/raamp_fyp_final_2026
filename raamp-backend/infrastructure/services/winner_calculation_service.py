"""
A/B Test Winner Calculation Service
====================================
Calculates composite engagement scores and determines test winners.
"""

import logging
from typing import Dict, Tuple
from domain.entities.ab_test_image import EngagementMetrics

logger = logging.getLogger(__name__)


class WinnerCalculationService:
    """Service for determining A/B test winners"""
    
    @staticmethod
    def calculate_composite_score(metrics: EngagementMetrics) -> float:
        """
        Calculate weighted composite engagement score.
        
        Formula: (likes×1) + (comments×3) + (shares×5) + (saves×4) + (reach×0.1) + (CTR×10)
        
        Weights reflect platform value:
        - Shares (5x): Highest signal of content quality
        - Saves (4x): Strong intent signal
        - Comments (3x): Active engagement
        - CTR (10x): Direct action signal
        - Reach (0.1x): Volume metric, less valuable
        - Likes (1x): Baseline engagement
        
        Args:
            metrics: EngagementMetrics object
            
        Returns:
            Composite score (float)
        """
        score = (
            (metrics.likes * 1) +
            (metrics.comments * 3) +
            (metrics.shares * 5) +
            (metrics.saves * 4) +
            (metrics.reach * 0.1) +
            (metrics.ctr * 10)
        )
        
        metrics.composite_score = score
        return score
    
    @staticmethod
    def calculate_delta(winner_score: float, loser_score: float) -> float:
        """
        Calculate performance delta as percentage.
        
        Formula: (winner - loser) / loser * 100
        
        Args:
            winner_score: Composite score of winning variant
            loser_score: Composite score of losing variant
            
        Returns:
            Delta percentage (float)
        """
        if loser_score == 0:
            return 100.0  # Avoid division by zero
        
        delta = ((winner_score - loser_score) / loser_score) * 100
        return round(delta, 2)
    
    @staticmethod
    def get_confidence_level(delta_percentage: float) -> str:
        """
        Determine confidence level based on delta.
        
        Rules:
        - < 10%: "too_close" - Results are inconclusive
        - 10-30%: "moderate" - Clear preference exists
        - > 30%: "clear_winner" - Statistically significant difference
        
        Args:
            delta_percentage: Performance gap percentage
            
        Returns:
            Confidence level string
        """
        if delta_percentage < 10:
            return "too_close"
        elif delta_percentage < 30:
            return "moderate"
        else:
            return "clear_winner"
    
    @staticmethod
    def determine_winner(
        variant_a_metrics: EngagementMetrics,
        variant_b_metrics: EngagementMetrics
    ) -> Dict[str, any]:
        """
        Determine A/B test winner with full analysis.
        
        Args:
            variant_a_metrics: Engagement metrics for variant A
            variant_b_metrics: Engagement metrics for variant B
            
        Returns:
            Dictionary with:
            - winner: "variant_a" or "variant_b"
            - winner_score: Composite score of winner
            - loser_score: Composite score of loser
            - delta_percentage: Performance gap
            - confidence_level: "clear_winner", "moderate", or "too_close"
            - analysis: Human-readable explanation
        """
        # Calculate composite scores
        score_a = WinnerCalculationService.calculate_composite_score(variant_a_metrics)
        score_b = WinnerCalculationService.calculate_composite_score(variant_b_metrics)
        
        # Determine winner
        if score_a > score_b:
            winner = "variant_a"
            winner_score = score_a
            loser_score = score_b
        else:
            winner = "variant_b"
            winner_score = score_b
            loser_score = score_a
        
        # Calculate delta
        delta = WinnerCalculationService.calculate_delta(winner_score, loser_score)
        
        # Get confidence level
        confidence = WinnerCalculationService.get_confidence_level(delta)
        
        # Generate analysis text
        analysis = WinnerCalculationService._generate_analysis(
            winner, winner_score, loser_score, delta, confidence
        )
        
        logger.info(f"Winner determined: {winner} with {delta}% advantage ({confidence} confidence)")
        
        return {
            "winner": winner,
            "winner_score": winner_score,
            "loser_score": loser_score,
            "delta_percentage": delta,
            "confidence_level": confidence,
            "analysis": analysis
        }
    
    @staticmethod
    def _generate_analysis(
        winner: str,
        winner_score: float,
        loser_score: float,
        delta: float,
        confidence: str
    ) -> str:
        """Generate human-readable analysis text"""
        
        winner_label = "Image A" if winner == "variant_a" else "Image B"
        loser_label = "Image B" if winner == "variant_a" else "Image A"
        
        if confidence == "clear_winner":
            return (
                f"🏆 **Clear Winner: {winner_label}**\n\n"
                f"{winner_label} outperformed {loser_label} by **{delta}%** (Composite: {winner_score:.0f} vs {loser_score:.0f}). "
                f"This is a statistically significant difference. Use {winner_label} for paid campaigns with high confidence."
            )
        elif confidence == "moderate":
            return (
                f"📊 **Moderate Winner: {winner_label}**\n\n"
                f"{winner_label} performed better by **{delta}%** (Composite: {winner_score:.0f} vs {loser_score:.0f}). "
                f"Results show a preference, but consider testing again with larger audience or longer duration for confirmation."
            )
        else:
            return (
                f"⚠️ **Too Close to Call**\n\n"
                f"Both variants performed similarly (Δ {delta}%). {winner_label} had a slight edge (Composite: {winner_score:.0f} vs {loser_score:.0f}), "
                f"but the difference is not statistically significant. Consider:\n"
                f"- Running the test longer (48-72 hours)\n"
                f"- Testing with a larger audience\n"
                f"- Using both variants in rotation"
            )


# Singleton instance
_winner_service_instance = None


def get_winner_service() -> WinnerCalculationService:
    """Get or create singleton winner calculation service"""
    global _winner_service_instance
    if _winner_service_instance is None:
        _winner_service_instance = WinnerCalculationService()
    return _winner_service_instance
