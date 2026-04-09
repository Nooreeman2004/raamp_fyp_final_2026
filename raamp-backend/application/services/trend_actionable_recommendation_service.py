from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from infrastructure.clients.llm_client import LLMClient
from application.services.viral_audio_provider import ViralAudioProvider

logger = logging.getLogger(__name__)


class TrendActionableRecommendationService:
    """
    Generates actionable recommendations JSON for a discovered trend.
    Keeps output shape flexible and stored on TrendDetectionModel.recommendations.
    """

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.audio_provider = ViralAudioProvider()

    @staticmethod
    def _safe_platform(platform: Optional[str]) -> str:
        p = (platform or "").strip().lower()
        if p in {"tiktok", "instagram", "facebook"}:
            return p
        return "instagram"

    @staticmethod
    def _derive_brand_tone(tone: Optional[str]) -> str:
        t = (tone or "").strip().lower()
        if "fun" in t or "play" in t:
            return "Funny"
        if "aesthetic" in t or "lux" in t or "premium" in t:
            return "Aesthetic"
        return "Professional"

    @staticmethod
    def _derive_budget(budget: Optional[str]) -> str:
        b = (budget or "").strip().lower()
        if b in {"low", "medium", "high"}:
            return b.title()
        return "Medium"

    @staticmethod
    def _fallback_actionable(*, keyword: str, location: str, niche: str, platform: str) -> Dict[str, Any]:
        """
        Deterministic fallback that still fills the UI (no LLM required).
        """
        kw = (keyword or "").strip()
        loc = (location or "GLOBAL").strip()
        niche_norm = (niche or "general").strip()
        platform_norm = TrendActionableRecommendationService._safe_platform(platform)

        return {
            "content_ideas": [
                f"Reel: 20s hook + 3 quick tips about “{kw}” for {niche_norm} customers in {loc}.",
                f"Carousel: 5 slides explaining “{kw}” + how it affects your audience in {loc}.",
                f"Story: poll + Q&A about “{kw}”, then a clear CTA (DM, link, visit).",
            ],
            "hashtags": [
                f"#{kw.replace(' ', '')[:24]}",
                f"#{niche_norm.replace(' ', '')[:24]}",
                f"#{loc.replace(' ', '')[:24]}",
                "#smallbusiness",
                f"#{platform_norm}",
            ],
            "content_format": {
                "type": "reel" if platform_norm == "instagram" else "carousel",
                "goal": "Discovery",
                "reason": "Fallback strategy (LLM unavailable): choose a format that typically maximizes reach quickly.",
            },
            "growth_hacks": [
                "Post within the next 2 hours, then repost to Stories 6–8 hours later.",
                "Ask a direct question in the caption and pin the best reply to drive comments.",
            ],
            "influencers": [
                {"persona": "Micro-creator", "platform": platform_norm, "relevance": "Already posts about this topic"},
                {"persona": "Local reviewer", "platform": platform_norm, "relevance": f"Audience in {loc}"},
            ],
            "notes": "fallback_strategy (no LLM required)",
        }

    async def _viral_audio(
        self,
        *,
        platform: str,
        location: str,
        niche: str,
        trend_keyword: str,
    ) -> List[Dict[str, Any]]:
        """
        Returns verified track + artist candidates from a real feed (Apple Music RSS).
        """
        try:
            tracks = await self.audio_provider.get_tracks(
                platform=platform,
                location=location,
                niche=niche,
                trend_keyword=trend_keyword,
                limit=2,
            )
            return tracks or []
        except Exception as e:
            logger.warning("viral_audio_generation_failed: %s", str(e))
            return []

    async def generate(
        self,
        *,
        location: str,
        trend_keywords: List[str],
        business_type: str,
        platform: str,
        brand_tone: str,
        age_group: str,
        niche: str,
        budget: str,
    ) -> Dict[str, Any]:
        platform_norm = self._safe_platform(platform)
        primary_keyword = (trend_keywords or [""])[0] if trend_keywords else ""

        # If LLM is unavailable, fail closed with a small, clearly marked payload.
        if not getattr(self.llm, "client", None):
            return {
                "campaign_suggestions": [],
                "actionable_recommendations": {
                    "error": "llm_unavailable",
                    "notes": "Connect OPENAI_API_KEY to generate actionable recommendations.",
                    **self._fallback_actionable(
                        keyword=str(primary_keyword or ""),
                        location=location,
                        niche=niche,
                        platform=platform_norm,
                    ),
                },
                "audio": self._audio_suggestions(platform=platform_norm),
            }

        # MASTER PROMPT (user-provided, enforced JSON-only)
        system_prompt = (
            "You are a highly professional and research-backed digital marketing strategist.\n"
            "Return ONLY valid JSON. Do not include markdown.\n"
            "Be specific and actionable. Avoid generic advice.\n"
        )

        # Ensure we keep the downstream contract intact by nesting under keys we own.
        trends_lines = chr(10).join(
            [f"{i + 1}. {t}" for i, t in enumerate((trend_keywords or [])[:10]) if str(t or "").strip()]
        )
        user_prompt = f"""
Current search trends in {location}:
{trends_lines}

Now generate the following specifically:

1. 3 unique content ideas: Tailored to the current trend and business type.
2. 5 trending hashtags: A mix of niche-specific and trend-driven tags.
3. Suggest best content format: Reels, Stories, Carousels, with a strong reason tied to engagement patterns.
4. Provide 2 non-generic growth hacks: Hyper-local strategies to increase reach.
5. 3 trending influencers: Provide influencer persona types (not real people), include style match, platform, and relevance to trend.
6. Campaign suggestions: Generate campaigns aligned with business type, platform, location, and brand tone.

Target Audience: Targeting {age_group} who are interested in {niche}.
Marketing Budget: The business has a {budget} budget.
Brand Tone: The brand voice should be {brand_tone}.
Business Type: {business_type}
Primary Platform: {platform_norm}

⚠️ Important:
- Don't be generic.
- Use current trend knowledge.
- Format output in JSON.
- Keep existing downstream contract (trendSignals, trendDetections) intact.

Output JSON with keys:
content_ideas, hashtags, content_format, growth_hacks, influencers, campaign_suggestions
""".strip()

        try:
            rec = await self.llm.generate_structured_json(system_prompt, user_prompt)
            if not isinstance(rec, dict):
                raise ValueError("llm_invalid_json")
        except Exception as e:
            logger.warning("Actionable recommendations generation failed (non-fatal): %s", str(e))
            rec = {
                "error": "llm_generation_failed",
                "notes": "Could not generate recommendations at this time.",
                **self._fallback_actionable(
                    keyword=str(primary_keyword or ""),
                    location=location,
                    niche=niche,
                    platform=platform_norm,
                ),
            }

        # Attach verified audio candidates separately (provider-backed)
        viral_audio = await self._viral_audio(
            platform=platform_norm,
            location=location,
            niche=niche,
            trend_keyword=str(primary_keyword or ""),
        )
        return {
            "campaign_suggestions": rec.get("campaign_suggestions") if isinstance(rec, dict) else [],
            "actionable_recommendations": rec,
            "viral_audio": viral_audio,
        }

