"""
Ad Brief Generation Service
============================
Generates paid ad campaign briefs from A/B test winners.
Integrates with business location data for geo-targeting.
"""

import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from domain.entities.ab_test_image import AdBriefRecommendation, EngagementMetrics
from infrastructure.repositories.business_repository import BusinessRepository

logger = logging.getLogger(__name__)


class AdBriefGenerationService:
    """Service for generating ad campaign briefs from test winners"""
    
    def __init__(self):
        self.business_repo = BusinessRepository()
    
    async def generate_ad_brief(
        self,
        user_id: str,
        winning_image_id: str,
        winning_metrics: EngagementMetrics,
        platform: str = "instagram",
        budget_daily: Optional[float] = None,
        duration_days: Optional[int] = None
    ) -> AdBriefRecommendation:
        """
        Generate a complete ad brief for the winning variant.
        
        Args:
            user_id: User ID
            winning_image_id: ID of the winning image
            winning_metrics: Engagement metrics from organic test
            platform: Target platform(s)
            budget_daily: Optional custom budget (USD/day)
            duration_days: Optional custom duration (3, 5, or 7 days)
            
        Returns:
            AdBriefRecommendation with targeting, budget, and creative guidance
        """
        # Get business location data
        business = await self.business_repo.get_by_user_id(user_id)
        
        if not business:
            raise ValueError("Business profile not found. Complete onboarding first.")
        
        # Extract geo targeting
        target_geo = self._extract_geo_target(business)
        
        # Determine audience segment
        audience_segment = self._determine_audience_segment(business, winning_metrics)
        
        # Calculate budget recommendations
        if not budget_daily:
            budget_daily = self._calculate_recommended_budget(platform, winning_metrics)
        
        if not duration_days:
            duration_days = self._calculate_recommended_duration(winning_metrics)
        
        total_spend = budget_daily * duration_days
        
        # Project performance
        projections = self._project_paid_performance(winning_metrics, budget_daily, duration_days)
        
        # Generate creative guidance
        creative_guidance = self._generate_creative_guidance(winning_metrics)
        
        # Build brief
        brief = AdBriefRecommendation(
            brief_id=str(uuid.uuid4()),
            result_id="",  # Set by caller
            winning_image_id=winning_image_id,
            target_geo=target_geo,
            audience_segment=audience_segment,
            suggested_budget_daily=budget_daily,
            suggested_duration_days=duration_days,
            total_spend=total_spend,
            estimated_reach=projections["reach"],
            estimated_clicks=projections["clicks"],
            estimated_ctr=projections["ctr"],
            estimated_cost_per_click=projections["cpc"],
            creative_hook=creative_guidance["hook"],
            cta_recommendation=creative_guidance["cta"],
            what_not_to_change=creative_guidance["preserve"],
            platform=self._normalize_platform(platform),
            created_at=datetime.utcnow()
        )
        
        logger.info(f"Generated ad brief {brief.brief_id} for user {user_id}")
        
        return brief
    
    def _extract_geo_target(self, business) -> str:
        """Extract geo targeting from business location"""
        if hasattr(business, 'city') and business.city:
            if hasattr(business, 'country') and business.country:
                return f"{business.city}, {business.country}"
            return business.city
        elif hasattr(business, 'formatted_address') and business.formatted_address:
            # Extract city from address
            parts = business.formatted_address.split(',')
            if len(parts) >= 2:
                return f"{parts[0].strip()}, {parts[-1].strip()}"
            return parts[0].strip()
        else:
            return "Local area (5km radius)"
    
    def _determine_audience_segment(self, business, metrics: EngagementMetrics) -> str:
        """Determine target audience based on business and organic performance"""
        # Default restaurant audience
        if hasattr(business, 'business_type') and 'cafe' in str(business.business_type).lower():
            return "18-44, food enthusiasts, mobile users"
        elif hasattr(business, 'business_type') and 'fine' in str(business.business_type).lower():
            return "25-54, upscale diners, mobile users"
        else:
            return "18-34, mobile users, food lovers"
    
    def _calculate_recommended_budget(self, platform: str, metrics: EngagementMetrics) -> float:
        """Calculate recommended daily budget based on platform and organic performance"""
        platform = platform.lower()
        
        # Base budgets by platform
        if "tiktok" in platform and "instagram" in platform:
            # Combined Instagram + TikTok
            return 30.0
        elif "tiktok" in platform:
            # TikTok requires higher minimum
            return 50.0
        else:
            # Instagram or Facebook
            return 30.0
    
    def _calculate_recommended_duration(self, metrics: EngagementMetrics) -> int:
        """Calculate recommended campaign duration (3, 5, or 7 days)"""
        # If high organic engagement, shorter test is sufficient
        if metrics.composite_score > 2000:
            return 3  # High confidence, quick test
        elif metrics.composite_score > 1000:
            return 5  # Moderate, standard test
        else:
            return 7  # Lower engagement, longer test for data
    
    def _project_paid_performance(
        self,
        organic_metrics: EngagementMetrics,
        budget_daily: float,
        duration_days: int
    ) -> Dict[str, Any]:
        """
        Project paid campaign performance based on organic results.
        
        Uses industry benchmarks:
        - CPM: $5-10 (cost per 1000 impressions)
        - CTR baseline: Organic CTR as reference
        - CPC: $0.16-$0.31 for food/beverage vertical
        """
        total_budget = budget_daily * duration_days
        
        # Estimate reach (impressions)
        # Assuming CPM of $7.50 average
        cpm = 7.50
        total_impressions = int((total_budget / cpm) * 1000)
        reach_min = int(total_impressions * 0.5)  # 50% unique reach
        reach_max = int(total_impressions * 0.8)  # 80% unique reach
        
        # Estimate CTR (use organic as baseline, expect paid to be similar or slightly lower)
        baseline_ctr = max(organic_metrics.ctr, 2.0)  # Minimum 2% CTR
        paid_ctr = baseline_ctr * 0.9  # Paid typically 10% lower than organic
        
        # Estimate clicks
        clicks_min = int((total_impressions * paid_ctr / 100) * 0.7)
        clicks_max = int((total_impressions * paid_ctr / 100) * 1.3)
        
        # Estimate CPC
        cpc_min = round((total_budget / clicks_max), 2)
        cpc_max = round((total_budget / clicks_min), 2)
        
        return {
            "reach": f"{reach_min//1000}k-{reach_max//1000}k",
            "clicks": f"{clicks_min}-{clicks_max}",
            "ctr": round(paid_ctr, 2),
            "cpc": f"${cpc_min:.2f}-${cpc_max:.2f}"
        }
    
    def _generate_creative_guidance(self, metrics: EngagementMetrics) -> Dict[str, str]:
        """Generate creative recommendations based on what worked organically"""
        
        # Determine what drove success
        if metrics.saves > metrics.shares:
            hook = "Lead with the visual element that drove saves — high-save content signals strong intent. Do not add text overlay that competes with the image."
        elif metrics.shares > metrics.saves:
            hook = "Lead with the shareable aspect — this content resonated for spreading. Keep the original composition intact."
        else:
            hook = "Lead with the visual elements that drove engagement. Maintain the original aesthetic that performed well."
        
        # CTA recommendation
        if metrics.ctr > 2.5:
            cta = "Single action only. \"Learn more\" or \"Shop now\" — match to your conversion goal. Avoid stacking two CTAs."
        else:
            cta = "Use a clear, single call-to-action. \"Learn more\" for awareness, \"Order now\" for conversions."
        
        # What not to change
        preserve = (
            "Composition, color palette, and subject framing — these are what drove the "
            f"{int(metrics.saves)} saves and {metrics.ctr:.1f}% CTR organically. "
            "Changing them for the ad breaks the success formula."
        )
        
        return {
            "hook": hook,
            "cta": cta,
            "preserve": preserve
        }
    
    def _normalize_platform(self, platform: str) -> str:
        """Normalize platform string for brief"""
        platform = platform.lower()
        if "instagram" in platform and "tiktok" in platform:
            return "instagram_tiktok"
        elif "instagram" in platform:
            return "instagram"
        elif "tiktok" in platform:
            return "tiktok"
        elif "facebook" in platform:
            return "facebook"
        else:
            return "instagram"


# Singleton instance
_ad_brief_service_instance = None


def get_ad_brief_service() -> AdBriefGenerationService:
    """Get or create singleton ad brief generation service"""
    global _ad_brief_service_instance
    if _ad_brief_service_instance is None:
        _ad_brief_service_instance = AdBriefGenerationService()
    return _ad_brief_service_instance
