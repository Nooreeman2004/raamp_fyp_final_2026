 
# Application Layer - Profit Proxy Service
import logging

logger = logging.getLogger(__name__)


class ProfitProxyService:
    """
    Service for estimating monetization potential (Profit Score).
    Combines arbitrage score, social score, and saturation score into a unified metric.
    """

    def calculate_profit_score(
        self,
        arbitrage_score: float,
        social_score: float,
        saturation_score: float,
        breakout_probability: float = 0.0,
        lifecycle_stage: str = "Mainstream"
    ) -> float:
        """
        Calculate normalized profit score (0-100).
        
        Higher profit score = Better monetization potential
        
        Args:
            arbitrage_score: Growth velocity / saturation ratio
            social_score: Social platform affinity & engagement potential
            saturation_score: Market competition (0-100)
            breakout_probability: Likelihood of breakout (0-100)
            lifecycle_stage: Current lifecycle (Emerging, Breakout, etc.)
            
        Returns:
            Profit score (0-100)
        """
        
        # Component 1: Arbitrage Score (40% weight)
        # High arbitrage = high velocity, low competition
        arbitrage_component = min(100, arbitrage_score * 4)  # Scale up
        
        # Component 2: Social Score (25% weight)
        # High social affinity = better organic reach
        social_component = social_score
        
        # Component 3: Inverse Saturation (20% weight)
        # Low saturation = higher profit potential
        # Invert: 100 - saturation
        competition_component = 100 - saturation_score
        
        # Component 4: Breakout Probability (15% weight)
        # Higher probability = better timing
        timing_component = breakout_probability
        
        # Weighted combination
        profit_score = (
            arbitrage_component * 0.40 +
            social_component * 0.25 +
            competition_component * 0.20 +
            timing_component * 0.15
        )
        
        # Lifecycle multiplier
        lifecycle_multipliers = {
            "Emerging": 1.2,      # 20% bonus for early entry
            "Breakout": 1.15,     # 15% bonus for momentum
            "Mainstream": 1.0,    # No modifier
            "Saturated": 0.7,     # 30% penalty for crowding
            "Declining": 0.5      # 50% penalty for decline
        }
        
        multiplier = lifecycle_multipliers.get(lifecycle_stage, 1.0)
        profit_score *= multiplier
        
        # Clip to 0-100 range
        return float(min(100, max(0, profit_score)))

    def get_profit_tier(self, profit_score: float) -> str:
        """
        Categorize profit score into tiers for frontend display.
        
        Args:
            profit_score: Calculated profit score
            
        Returns:
            Tier label: Gold Mine, High Potential, Moderate, Low, Avoid
        """
        if profit_score >= 80:
            return "Gold Mine"
        elif profit_score >= 65:
            return "High Potential"
        elif profit_score >= 45:
            return "Moderate"
        elif profit_score >= 25:
            return "Low"
        else:
            return "Avoid"

    def get_profit_color(self, profit_score: float) -> str:
        """
        Return color code for profit score visualization.
        
        Args:
            profit_score: Calculated profit score
            
        Returns:
            Hex color code
        """
        if profit_score >= 80:
            return "#10b981"  # Green - Gold Mine
        elif profit_score >= 65:
            return "#22c55e"  # Light Green - High
        elif profit_score >= 45:
            return "#f59e0b"  # Amber - Moderate
        elif profit_score >= 25:
            return "#f97316"  # Orange - Low
        else:
            return "#ef4444"  # Red - Avoid

    def estimate_roi_multiplier(
        self,
        profit_score: float,
        lifecycle_stage: str,
        avg_volume: float
    ) -> float:
        """
        Estimate potential ROI multiplier for paid campaigns.
        
        Args:
            profit_score: Calculated profit score
            lifecycle_stage: Current lifecycle
            avg_volume: Average search volume
            
        Returns:
            Estimated ROI multiplier (e.g., 2.5x means 250% return)
        """
        # Base ROI from profit score
        # Score 100 = 5x ROI, Score 0 = 0.5x ROI
        base_roi = 0.5 + (profit_score / 100) * 4.5
        
        # Lifecycle adjustment
        if lifecycle_stage == "Emerging":
            base_roi *= 1.3  # Early movers get better ROI
        elif lifecycle_stage == "Breakout":
            base_roi *= 1.2
        elif lifecycle_stage == "Saturated":
            base_roi *= 0.6
        elif lifecycle_stage == "Declining":
            base_roi *= 0.3
        
        # Volume adjustment (higher volume = more scale potential)
        if avg_volume > 70:
            base_roi *= 1.1
        elif avg_volume < 20:
            base_roi *= 0.8
        
        return round(base_roi, 2)

    def calculate_effort_score(
        self,
        saturation_score: float,
        social_score: float,
        lifecycle_stage: str
    ) -> str:
        """
        Estimate content creation & marketing effort required.
        
        Args:
            saturation_score: Market competition
            social_score: Social platform fit
            lifecycle_stage: Current lifecycle
            
        Returns:
            Effort level: Low, Medium, High
        """
        # High saturation = high effort needed to compete
        # Low social score = high effort to gain traction
        
        effort_points = 0
        
        # Saturation factor
        if saturation_score > 70:
            effort_points += 2
        elif saturation_score > 50:
            effort_points += 1
        
        # Social score factor (inverse)
        if social_score < 40:
            effort_points += 2
        elif social_score < 60:
            effort_points += 1
        
        # Lifecycle factor
        if lifecycle_stage in ["Saturated", "Declining"]:
            effort_points += 2
        elif lifecycle_stage == "Mainstream":
            effort_points += 1
        
        # Determine effort level
        if effort_points >= 4:
            return "High"
        elif effort_points >= 2:
            return "Medium"
        else:
            return "Low"

    def get_monetization_channels(
        self,
        social_score: float,
        platform_bias: dict,
        lifecycle_stage: str
    ) -> list:
        """
        Recommend monetization channels based on trend characteristics.
        
        Args:
            social_score: Social platform affinity
            platform_bias: Platform scores (instagram, tiktok, google, etc.)
            lifecycle_stage: Current lifecycle
            
        Returns:
            List of recommended channels
        """
        channels = []
        
        # Organic social if high social score
        if social_score > 60:
            if platform_bias.get("instagram", 0) > 0.5:
                channels.append("Instagram Organic")
            if platform_bias.get("tiktok", 0) > 0.5:
                channels.append("TikTok Organic")
        
        # Paid search for search-heavy trends
        if platform_bias.get("google", 0) > 0.6:
            channels.append("Google Ads")
        
        # Facebook ads for mainstream/mature trends
        if lifecycle_stage in ["Mainstream", "Breakout"]:
            channels.append("Facebook Ads")
        
        # Influencer marketing for emerging visual trends
        if lifecycle_stage == "Emerging" and social_score > 70:
            channels.append("Influencer Marketing")
        
        # Affiliate marketing for commercial keywords
        if platform_bias.get("google", 0) > 0.5:
            channels.append("Affiliate Content")
        
        # Default fallback
        if not channels:
            channels.append("Content Marketing")
        
        return channels[:3]  # Return top 3
