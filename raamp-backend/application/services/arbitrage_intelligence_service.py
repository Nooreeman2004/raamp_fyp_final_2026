
# Application Layer - Arbitrage Intelligence Service
import logging
import json
from typing import List, Dict, Any, Optional
from infrastructure.clients.llm_client import LLMClient
from presentation.schemas.arbitrage_schemas import UserProfileSchema, TrendSignalInputSchema, CampaignRecommendationResponse

logger = logging.getLogger(__name__)

class ArbitrageIntelligenceService:
    """Service to convert trend signals into marketing recommendations using LLM"""
    
    def __init__(self):
        self.llm_client = LLMClient()
        self.system_prompt = """
        You are the 'Arbitrage Intelligence Engine', an expert marketing strategist for RAAMP.
        Your goal is to identify the highest ROI marketing opportunities based on trend data.
        
        RULES:
        1. Explanations must be non-technical. Avoid jargon like 'Z-score', 'EWMA', 'vector embeddings'.
        2. Focus on the 'WHY' from a business perspective (e.g. 'This is a gold mine because demand is spiking but no competitors are advertising here yet').
        3. Recommendations must be actionable for small and medium businesses.
        4. Align platform suggestions with the trend's characteristics (e.g. visual trends → Instagram, research trends → Google Search/Blog).
        5. Return ONLY a JSON object with the structure defined below.
        
        RESPONSE FORMAT:
        {
          "recommendations": [
            {
              "trend_name": "string",
              "campaign_idea": "short catchy title",
              "recommended_platform": "Instagram | Facebook | Google Search | TikTok",
              "reasoning": "Simple explanation of the arbitrage opportunity",
              "expected_marketing_goal": "Brand Awareness | Conversion | Lead Gen",
              "suggested_hooks": ["Hook 1", "Hook 2"],
              "estimated_effort": "Low | Medium | High",
              "priority": 1-10
            }
          ],
          "context": "A 1-sentence summary of the market landscape for the user's niche."
        }
        """

    async def generate_recommendations(
        self, 
        trends: List[TrendSignalInputSchema], 
        user_profile: UserProfileSchema
    ) -> Dict[str, Any]:
        """Generate recommendations using Layer 2 intelligence"""
        
        # Prepare data for prompt
        trends_info = [t.model_dump() for t in trends]
        user_info = user_profile.model_dump()
        
        user_prompt = f"""
        USER PROFILE:
        Niche: {user_info['niche']}
        Location: {user_info['location']}
        Target Audience: {user_info['target_audience']}
        
        CURRENT TREND SIGNALS:
        {json.dumps(trends_info, indent=2)}
        
        Identify the top 3 arbitrage opportunities and generate campaign recommendations.
        """
        
        try:
            result = await self.llm_client.generate_structured_json(self.system_prompt, user_prompt)
            if result:
                return result
        except Exception as e:
            logger.error("Failed to generate recommendations via LLM: %s", str(e))
            
        # Fallback Logic
        return self._generate_fallback(trends, user_profile)

    def _generate_fallback(self, trends: List[TrendSignalInputSchema], user_profile: UserProfileSchema) -> Dict[str, Any]:
        """Simple rule-based fallback if LLM is unavailable"""
        logger.info("Generating fallback recommendations")
        recommendations = []
        
        for t in trends[:3]:
            best_platform = t.platform_fit[0] if t.platform_fit else "Google"
            recommendations.append({
                "trend_name": t.keyword,
                "campaign_idea": f"The {t.keyword} Jumpstart",
                "recommended_platform": best_platform,
                "reasoning": f"This trend is currently {t.velocity_label.lower()} velocity with {t.saturation_label.lower()} competition.",
                "expected_marketing_goal": "Traffic & Awareness",
                "suggested_hooks": [f"Looking for {t.keyword}?", f"Why {t.keyword} is trending right now."],
                "estimated_effort": "Medium",
                "priority": 5
            })
            
        return {
            "recommendations": recommendations,
            "context": f"Market analysis suggests focusing on {trends[0].keyword if trends else 'current niche trends'}."
        }
