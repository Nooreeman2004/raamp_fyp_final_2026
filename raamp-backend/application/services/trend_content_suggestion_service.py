
# Application Layer - Trend Content Suggestion Service
import logging
from typing import Dict, Optional
from datetime import datetime
from infrastructure.clients.llm_client import LLMClient
from infrastructure.database.models.content_suggestion_cache_model import ContentSuggestionCacheModel

logger = logging.getLogger(__name__)


class TrendContentSuggestionService:
    """
    Service for generating AI-powered content and campaign suggestions for trends.
    Uses existing LLM client to generate actionable marketing ideas.
    """

    def __init__(self):
        self.llm_client = LLMClient()

    async def generate_content_suggestions(
        self,
        keyword: str,
        niche: str,
        lifecycle_stage: str,
        profit_score: float,
        social_score: float,
        saturation_score: float,
        platform_bias: Dict[str, float]
    ) -> Dict:
        """
        Generate comprehensive content and campaign suggestions for a trending keyword.
        Uses caching to avoid duplicate LLM API calls (24h TTL).
        
        Args:
            keyword: The trending keyword
            niche: Business niche
            lifecycle_stage: Current lifecycle stage
            profit_score: Monetization potential
            social_score: Social platform affinity
            saturation_score: Market competition
            platform_bias: Platform scores
            
        Returns:
            Dict containing video_ideas, hooks, hashtags, campaign_angle, influencer_strategy
        """
        
        # Check cache first (24h TTL)
        cache_key_normalized = keyword.lower().strip()
        cached = await ContentSuggestionCacheModel.find_one({
            "keyword": cache_key_normalized,
            "niche": niche
        })
        
        if cached and not cached.is_expired:
            logger.info("Cache hit for keyword '%s' in niche '%s'", cache_key_normalized, niche)
            return {
                "video_ideas": cached.video_ideas,
                "hooks": cached.hooks,
                "hashtags": cached.hashtags,
                "campaign_angle": cached.campaign_angle,
                "influencer_strategy": cached.influencer_strategy
            }
        
        # Cache miss - generate new suggestions
        if not self.llm_client.client:
            # Fail-closed: do not return templated suggestions that look "real".
            # The router will translate this into a user-friendly 503.
            raise RuntimeError("llm_unavailable")
        
        # Determine primary platform
        primary_platform = max(platform_bias, key=platform_bias.get) if platform_bias else "instagram"
        
        # Build context-rich prompt
        system_prompt = """You are a marketing strategy expert specializing in trend-based content creation.
Generate actionable, specific marketing suggestions based on the trend data provided.
Return your response as valid JSON with the following structure:
{
    "video_ideas": ["idea1", "idea2", "idea3"],
    "hooks": ["hook1", "hook2", "hook3"],
    "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5", "#tag6", "#tag7", "#tag8", "#tag9", "#tag10"],
    "campaign_angle": "detailed campaign strategy",
    "influencer_strategy": "influencer partnership approach"
}"""

        user_prompt = f"""Generate marketing content suggestions for this trending opportunity:

TREND DATA:
- Keyword: "{keyword}"
- Niche: {niche}
- Lifecycle Stage: {lifecycle_stage}
- Profit Score: {profit_score:.1f}/100
- Social Score: {social_score:.1f}/100
- Competition: {saturation_score:.1f}/100
- Primary Platform: {primary_platform.title()}

REQUIREMENTS:
1. VIDEO IDEAS: Generate 3 specific short-form video concepts (15-60 seconds) optimized for {primary_platform}. Make them actionable and trend-specific.

2. HOOKS: Create 3 attention-grabbing opening lines that stop the scroll. Use curiosity gaps, bold claims, or pattern interrupts.

3. HASHTAGS: Provide 10 optimized hashtags mixing:
   - 3 high-volume trending tags
   - 4 medium-volume niche tags
   - 3 low-competition long-tail tags

4. CAMPAIGN ANGLE: Design a complete paid campaign strategy considering:
   - Ad platform recommendation
   - Target audience definition
   - Budget allocation approach
   - Expected conversion funnel

5. INFLUENCER STRATEGY: Suggest micro-influencer partnership approach:
   - Influencer tier to target
   - Collaboration format
   - Compensation structure
   - Expected reach

Make everything specific to "{keyword}" in the {niche} niche with {lifecycle_stage} lifecycle stage."""

        try:
            result = await self.llm_client.generate_structured_json(system_prompt, user_prompt)
            
            if not result:
                raise RuntimeError("llm_empty_result")
            
            # Validate structure
            required_keys = ["video_ideas", "hooks", "hashtags", "campaign_angle", "influencer_strategy"]
            if all(key in result for key in required_keys):
                # Cache the successful result (24h TTL)
                try:
                    cache_entry = ContentSuggestionCacheModel(
                        keyword=cache_key_normalized,
                        niche=niche,
                        lifecycle_stage=lifecycle_stage,
                        video_ideas=result["video_ideas"],
                        hooks=result["hooks"],
                        hashtags=result["hashtags"],
                        campaign_angle=result["campaign_angle"],
                        influencer_strategy=result["influencer_strategy"]
                    )
                    await cache_entry.insert()
                    logger.info("Cached suggestions for keyword '%s' in niche '%s'", cache_key_normalized, niche)
                except Exception as cache_error:
                    logger.warning("Failed to cache suggestions: %s", str(cache_error))
                
                return result
            else:
                logger.warning("LLM response missing required keys, using fallback")
                raise RuntimeError("llm_invalid_shape")
                
        except Exception as e:
            logger.error("Failed to generate AI suggestions: %s", str(e))
            raise

    def _generate_fallback_suggestions(self, keyword: str, niche: str) -> Dict:
        """
        Generate rule-based suggestions when LLM is unavailable.
        
        Args:
            keyword: The trending keyword
            niche: Business niche
            
        Returns:
            Basic content suggestions
        """
        keyword_clean = keyword.replace(" ", "").lower()
        
        return {
            "video_ideas": [
                f"Why everyone is talking about {keyword} right now",
                f"3 ways to leverage {keyword} in your {niche} business",
                f"I tried {keyword} for 30 days - here's what happened"
            ],
            "hooks": [
                f"Stop scrolling. {keyword} is about to change everything.",
                f"Nobody is talking about this {keyword} opportunity...",
                f"I made $X using {keyword} - here's how you can too"
            ],
            "hashtags": [
                f"#{keyword_clean}",
                f"#{niche.lower().replace(' ', '')}",
                "#trending",
                "#viral",
                "#marketing",
                "#growth",
                "#business",
                "#entrepreneur",
                "#contentcreator",
                "#socialmedia"
            ],
            "campaign_angle": f"Run a targeted {niche} campaign focusing on {keyword}. Start with organic content to test engagement, then scale with micro-influencer partnerships and paid ads on the highest-performing platform. Use urgency messaging to capitalize on the trend momentum.",
            "influencer_strategy": f"Partner with 5-10 micro-influencers (10k-50k followers) in the {niche} space. Offer product/service in exchange for authentic content featuring {keyword}. Focus on engagement rate over follower count. Run a 2-week campaign with trackable promo codes."
        }

    async def get_cached_suggestions(
        self,
        keyword: str,
        user_id: str
    ) -> Optional[Dict]:
        """
        Retrieve cached content suggestions from database.
        
        Args:
            keyword: The trending keyword
            user_id: User email
            
        Returns:
            Cached suggestions or None
        """
        # Check if we've stored suggestions in the trend detection model
        # You could extend TrendDetectionModel to include a content_suggestions field
        # For now, we'll regenerate on demand
        return None

    async def save_suggestions(
        self,
        keyword: str,
        user_id: str,
        suggestions: Dict
    ):
        """
        Cache suggestions in database for future retrieval.
        
        Args:
            keyword: The trending keyword
            user_id: User email
            suggestions: Generated suggestions
        """
        # This could be extended to save to a dedicated collection
        # or add to TrendDetectionModel
        logger.info(f"Suggestions generated for {keyword} (user: {user_id})")
        pass

    def get_suggestion_quality_score(self, suggestions: Dict) -> float:
        """
        Score the quality of generated suggestions (0-100).
        
        Args:
            suggestions: Generated suggestions dict
            
        Returns:
            Quality score
        """
        score = 0.0
        
        # Check completeness
        if suggestions.get("video_ideas") and len(suggestions["video_ideas"]) >= 3:
            score += 20
        if suggestions.get("hooks") and len(suggestions["hooks"]) >= 3:
            score += 20
        if suggestions.get("hashtags") and len(suggestions["hashtags"]) >= 10:
            score += 20
        if suggestions.get("campaign_angle"):
            score += 20
        if suggestions.get("influencer_strategy"):
            score += 20
        
        return min(100, score)
