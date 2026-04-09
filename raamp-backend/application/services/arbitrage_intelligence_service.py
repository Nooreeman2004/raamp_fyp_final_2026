
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

    async def _load_brand_context(self, user_email: Optional[str]) -> Dict[str, Any]:
        """
        Load brand alignment context for the user (best-effort).
        Does not raise; returns {} if not available.
        """
        try:
            from infrastructure.database.models.business_model import BusinessModel

            if not user_email:
                return {}

            biz = await BusinessModel.find_one(BusinessModel.user_id == user_email)
            if not biz:
                return {}

            return {
                "business_name": biz.business_name,
                "tagline": biz.tagline,
                "tone_of_voice": biz.tone_of_voice,
                "primary_color": biz.primary_color,
                "secondary_color": biz.secondary_color,
                "brand_colors": list(biz.brand_colors or []),
                "restaurant_theme": biz.restaurant_theme,
                "specialties": list(biz.specialties or []),
                "business_type": biz.business_type,
                "description": biz.description,
                # Geo-Intent wiring fields
                "latitude": biz.latitude,
                "longitude": biz.longitude,
                "is_indoor": biz.is_indoor,
                "targeting_radius_m": biz.targeting_radius_m,
            }
        except Exception as e:
            logger.warning("Brand context load failed (non-fatal): %s", str(e))
            return {}

    @staticmethod
    def _format_brand_context_block(ctx: Dict[str, Any]) -> str:
        if not ctx:
            return ""
        lines: List[str] = []
        if ctx.get("business_name"):
            lines.append(f"Business Name: {ctx['business_name']}")
        if ctx.get("tagline"):
            lines.append(f"Tagline: {ctx['tagline']}")
        if ctx.get("tone_of_voice"):
            lines.append(f"Tone of Voice: {ctx['tone_of_voice']}")
        if ctx.get("restaurant_theme"):
            lines.append(f"Theme: {ctx['restaurant_theme']}")
        if ctx.get("business_type"):
            lines.append(f"Business Type: {ctx['business_type']}")
        if ctx.get("specialties"):
            lines.append(f"Specialties: {', '.join(ctx['specialties'])}")
        # Colors: include both primary/secondary and palette list if present
        colors = []
        if ctx.get("primary_color"):
            colors.append(str(ctx["primary_color"]))
        if ctx.get("secondary_color"):
            colors.append(str(ctx["secondary_color"]))
        for c in (ctx.get("brand_colors") or []):
            if c and c not in colors:
                colors.append(str(c))
        if colors:
            lines.append(f"Brand Colors: {', '.join(colors)}")
        if ctx.get("description"):
            lines.append(f"Brand Description: {ctx['description']}")

        if not lines:
            return ""
        return "BRAND CONTEXT (use for voice + consistency):\n" + "\n".join(lines) + "\n"

    @staticmethod
    def _derive_local_intent_keywords(place_types: List[str], rising_queries: List[str]) -> List[str]:
        mapping = {
            "restaurant": ["dining", "food delivery", "takeout"],
            "cafe": ["coffee", "brunch", "takeout"],
            "bakery": ["desserts", "fresh bread", "takeout"],
            "gym": ["fitness", "workout", "wellness"],
            "park": ["outdoors", "family", "weekend plans"],
            "shopping_mall": ["retail", "fashion", "deals"],
            "clothing_store": ["fashion", "streetwear", "deals"],
            "supermarket": ["groceries", "daily essentials", "offers"],
            "transit_station": ["commute", "grab-and-go", "near me"],
            "pharmacy": ["health", "wellness", "urgent needs"],
        }
        out: List[str] = []
        for t in place_types or []:
            for k, vals in mapping.items():
                if t == k:
                    out.extend(vals)
        out.extend([q for q in (rising_queries or []) if q])
        # de-dupe preserve order
        dedup: List[str] = []
        seen = set()
        for x in out:
            xx = str(x).strip()
            if not xx:
                continue
            lx = xx.lower()
            if lx in seen:
                continue
            seen.add(lx)
            dedup.append(xx)
            if len(dedup) >= 5:
                break
        return dedup

    async def _load_local_context_block(
        self,
        *,
        user_email: str,
        brand_ctx: Dict[str, Any],
        trend_keywords: List[str],
        user_profile: Dict[str, Any],
    ) -> str:
        """
        Best-effort Geo-Intent snapshot for localization (never raises).
        """
        try:
            lat = brand_ctx.get("latitude")
            lng = brand_ctx.get("longitude")
            if lat is None or lng is None:
                return ""

            from fastapi import BackgroundTasks
            from application.services.geo_intent_service import GeoIntentService
            from infrastructure.database.models.trend_signal_model import TrendSignalModel

            radius_m = int(brand_ctx.get("targeting_radius_m") or 5000)
            is_indoor = bool(brand_ctx.get("is_indoor", True))

            top_keywords = [k for k in trend_keywords if k][:3]
            if not top_keywords:
                return ""

            geo = GeoIntentService()
            geo_res = await geo.compute(
                business_id=f"arbitrage_{user_email}",
                keywords=top_keywords,
                latitude=float(lat),
                longitude=float(lng),
                radius=radius_m,
                is_indoor=is_indoor,
                background_tasks=BackgroundTasks(),
                user_id=user_email,
                skip_credits=True,
            )

            persona_split = geo_res.get("persona_split") or []
            heat_score = geo_res.get("score")
            place_types = list(geo_res.get("place_types") or [])[:5]

            dominant = "General Audience"
            dominant_pct = 0
            if persona_split and isinstance(persona_split, list):
                try:
                    sorted_p = sorted(persona_split, key=lambda x: x.get("pct", 0), reverse=True)
                    dominant = sorted_p[0].get("type") or dominant
                    dominant_pct = int(sorted_p[0].get("pct") or 0)
                except Exception:
                    pass

            # Best-effort rising queries from recent signals (top 2)
            rising: List[str] = []
            try:
                kw0 = top_keywords[0]
                s = (
                    await TrendSignalModel.find(
                        TrendSignalModel.user_email == user_email,
                        TrendSignalModel.fetch_status == "completed",
                    )
                    .sort(-TrendSignalModel.created_at)
                    .first_or_none()
                )
                if s and isinstance(s.rising_queries, dict):
                    qlist = s.rising_queries.get(kw0) or []
                    for q in qlist[:2]:
                        if isinstance(q, dict) and q.get("query"):
                            rising.append(str(q["query"]))
            except Exception:
                pass

            intent = self._derive_local_intent_keywords(place_types, rising)

            lines = [
                "LOCAL CONTEXT:",
                f"- Dominant persona: {dominant} ({dominant_pct}%)",
            ]
            if isinstance(heat_score, (int, float)):
                lines.append(f"- Area heat score: {int(round(float(heat_score)))}/100")
            if place_types:
                lines.append(f"- Nearby place types: {', '.join(place_types[:5])}")
            if intent:
                lines.append(f"- Local intent signals: {', '.join(intent)}")

            return "\n".join(lines) + "\n"
        except Exception as e:
            logger.info("Local context load failed (non-fatal): %s", str(e))
            return ""

    async def generate_recommendations(
        self, 
        trends: List[TrendSignalInputSchema], 
        user_profile: UserProfileSchema,
        user_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Generate recommendations using Layer 2 intelligence"""
        
        # Prepare data for prompt
        trends_info = [t.model_dump() for t in trends]
        user_info = user_profile.model_dump()

        brand_ctx = await self._load_brand_context(user_email)
        brand_block = self._format_brand_context_block(brand_ctx)

        local_block = ""
        if user_email:
            # use trend keywords in rank order provided
            local_block = await self._load_local_context_block(
                user_email=user_email,
                brand_ctx=brand_ctx,
                trend_keywords=[t.keyword for t in trends],
                user_profile=user_info,
            )
        
        user_prompt = f"""
        USER PROFILE:
        Niche: {user_info['niche']}
        Location: {user_info['location']}
        Target Audience: {user_info['target_audience']}

        {brand_block}

        {local_block}
        
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
