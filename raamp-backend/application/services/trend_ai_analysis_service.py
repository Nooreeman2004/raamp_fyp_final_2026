from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from infrastructure.clients.llm_client import LLMClient
from infrastructure.database.models.business_model import BusinessModel
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_ai_analysis_model import TrendAIAnalysisModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from infrastructure.utils.obs import emit_event

from application.services.social_trend_service import SocialTrendService

logger = logging.getLogger(__name__)


class TrendAIAnalysisService:
    def __init__(self) -> None:
        self.llm = LLMClient()
        self.hashtags = SocialTrendService()

    async def get_analysis(self, trend_id: str, user_id: str) -> Optional[TrendAIAnalysisModel]:
        return await TrendAIAnalysisModel.find_one({"trend_id": str(trend_id), "user_id": str(user_id)})

    async def regenerate_analysis(self, trend_id: str, user_id: str) -> TrendAIAnalysisModel:
        # Overwrite by deleting existing (unique index ensures single doc).
        existing = await self.get_analysis(trend_id, user_id)
        if existing:
            try:
                await existing.delete()
            except Exception:
                pass
        return await self.generate_analysis(trend_id, user_id)

    async def _top_keyword_for_trend(self, trend_id: str, user_id: str) -> str:
        # Prefer latest detection for this trend_signal_id.
        try:
            det = (
                await TrendDetectionModel.find(
                    {"user_id": str(user_id), "trend_signal_id": str(trend_id)}
                )
                .sort("-detected_at")
                .first_or_none()
            )
            if det and getattr(det, "keyword", None):
                return str(det.keyword)
        except Exception:
            pass
        return ""

    async def _fallback_keyword_from_signal(self, trend_id: str) -> str:
        """
        If there are no TrendDetectionModel records for a trend_id yet, fall back to
        the TrendSignalModel.keywords[0] that seeded the scan.

        This prevents generate_analysis() from failing early when detection rows
        haven't been created/persisted for the trend.
        """
        try:
            sig = await TrendSignalModel.get(trend_id)
            if not sig:
                return ""
            kws = list(getattr(sig, "keywords", []) or [])
            if not kws:
                return ""
            first = str(kws[0] or "").strip()
            return first
        except Exception:
            return ""

    async def _brand_snapshot(self, user_id: str) -> Dict[str, Any]:
        """
        Snapshot brand voice + specialties + geo fields from BusinessModel (best-effort).
        """
        try:
            biz = await BusinessModel.find_one({"user_id": str(user_id)})
            if not biz:
                return {}
            return {
                "business_name": getattr(biz, "business_name", None),
                "tagline": getattr(biz, "tagline", None),
                "tone_of_voice": getattr(biz, "tone_of_voice", None),
                "primary_color": getattr(biz, "primary_color", None),
                "secondary_color": getattr(biz, "secondary_color", None),
                "brand_colors": list(getattr(biz, "brand_colors", []) or []),
                "restaurant_theme": getattr(biz, "restaurant_theme", None),
                "specialties": list(getattr(biz, "specialties", []) or []),
                "business_type": getattr(biz, "business_type", None),
                "description": getattr(biz, "description", None),
                "country": getattr(biz, "country", None),
                "city": getattr(biz, "city", None),
            }
        except Exception as e:
            logger.info("brand_snapshot_failed (non-fatal): %s", str(e))
            return {}

    async def generate_analysis(self, trend_id: str, user_id: str) -> TrendAIAnalysisModel:
        trend_id = str(trend_id)
        user_id = str(user_id)

        # Create pending placeholder (helps ai_analysis_status show pending).
        placeholder = TrendAIAnalysisModel(
            trend_id=trend_id,
            user_id=user_id,
            trend_keyword="",
            generated_at=datetime.utcnow(),
            status="pending",
            brand_voice_used=await self._brand_snapshot(user_id),
            model_version=getattr(self.llm, "model", None),
        )
        await placeholder.insert()

        try:
            keyword = (await self._top_keyword_for_trend(trend_id, user_id)).strip()
            if not keyword:
                keyword = (await self._fallback_keyword_from_signal(trend_id)).strip()
            if not keyword:
                raise ValueError("no_trend_keyword_available")

            brand = placeholder.brand_voice_used or {}
            specialties = [s for s in (brand.get("specialties") or []) if isinstance(s, str) and s.strip()]
            geo = (brand.get("city") or brand.get("country") or "PK") if isinstance(brand, dict) else "PK"

            system_prompt = (
                "You are an elite trend arbitrage strategist for small businesses.\n"
                "Return ONLY valid JSON. No markdown.\n"
                "Be specific, local, and non-generic.\n"
            )

            user_prompt = f"""
Generate a complete trend intelligence analysis for this user and trend.

TREND:
- Keyword: {keyword}
- TrendID: {trend_id}

BUSINESS CONTEXT (snapshot, use for brand voice):
{brand}

REQUIREMENTS:
- executive_summary: 2-3 sentences, why it matters to THIS business.
- opportunity_score: urgency/relevance/competition integers 0-100.
- opportunity_window: a plain-english status for a business owner [e.g., 'Extreme Early Access', 'Rising High', 'Gold Rush', 'Window Closing', 'Mainstream Peak'].
- market_context: what's driving it right now.
- risk_level: one of [flash, sustained, uncertain]
- risk_explanation: 1-2 sentences.
- competitor_gap: boolean, are competitors likely under-covering this?

STRATEGY:
- content_angles: 3-5 angles tailored to niche/specialties.
- platform_recommendations: list of objects {{platform, format, reason}}.
- posting_window: string (timing guidance).

INTELLIGENCE GRID (same call):
- campaign_ideas: list of 3 objects {{title, description, platform, urgency_tag}}.
- content_format_recommendation: object {{primary_format, reasoning: [..], secondary_format}}.
- growth_hacks: list of 2 tactics specific to geo '{geo}' and niche/specialties {specialties}.

Output JSON with keys:
executive_summary, opportunity_score, market_context, risk_level, risk_explanation, competitor_gap,
content_angles, platform_recommendations, posting_window,
campaign_ideas, content_format_recommendation, growth_hacks
""".strip()

            if not getattr(self.llm, "client", None):
                raise RuntimeError("llm_unavailable")

            payload = await self.llm.generate_structured_json(system_prompt, user_prompt)
            if not isinstance(payload, dict):
                raise RuntimeError("llm_invalid_json")

            # Hashtag pack (category-aware, not niche-based)
            # Detect trend category from keyword content
            keyword_lower = keyword.lower()
            trend_category_map = {
                "sports": ["cricket", "football", "soccer", "basketball", "tennis", "match", "game", "vs", "league", "tournament", "psl", "ipl"],
                "fashion": ["fashion", "style", "outfit", "ootd", "clothing", "apparel", "wear", "dress"],
                "food": ["food", "recipe", "cooking", "meal", "dish", "cuisine", "delicious", "restaurant"],
                "tech": ["tech", "technology", "ai", "software", "app", "digital", "innovation"],
                "fitness": ["fitness", "workout", "gym", "exercise", "health", "training"],
                "beauty": ["beauty", "makeup", "skincare", "cosmetic", "hair"],
                "travel": ["travel", "trip", "vacation", "destination", "tourism"],
            }
            
            detected_category = None
            for category, patterns in trend_category_map.items():
                if any(pattern in keyword_lower for pattern in patterns):
                    detected_category = category
                    break
            
            # Generate hashtags based on trend category, not user's business niche
            if detected_category:
                # Use category-specific terms for hashtag generation
                category_terms = {
                    "sports": ["sports", "game", "competition", "athlete", "team"],
                    "fashion": ["fashion", "style", "ootd", "trendy", "outfit"],
                    "food": ["foodie", "foodlover", "instafood", "delicious", "yummy"],
                    "tech": ["tech", "technology", "innovation", "digital", "future"],
                    "fitness": ["fitness", "workout", "health", "fitfam", "training"],
                    "beauty": ["beauty", "makeup", "skincare", "glam", "beautytips"],
                    "travel": ["travel", "wanderlust", "explore", "adventure", "travelgram"],
                }
                hashtag_seeds = [keyword] + category_terms.get(detected_category, [])
            else:
                # Fallback: use keyword + specialties only if no category detected
                hashtag_seeds = [keyword] + specialties
            
            derived_tags = self.hashtags.generate_hashtags(hashtag_seeds, count=15)
            primary = derived_tags[:5]
            secondary = derived_tags[5:10]
            niche_tags = derived_tags[10:15]

            update: Dict[str, Any] = {
                "trend_keyword": keyword,
                "status": "completed",
                "generated_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "executive_summary": str(payload.get("executive_summary") or "").strip() or None,
                "opportunity_score": payload.get("opportunity_score") or {},
                "opportunity_window": str(payload.get("opportunity_window") or "").strip() or None,
                "market_context": str(payload.get("market_context") or "").strip() or None,
                "risk_level": payload.get("risk_level"),
                "risk_explanation": str(payload.get("risk_explanation") or "").strip() or None,
                "competitor_gap": payload.get("competitor_gap"),
                "content_angles": payload.get("content_angles") or [],
                "platform_recommendations": payload.get("platform_recommendations") or [],
                "posting_window": str(payload.get("posting_window") or "").strip() or None,
                "campaign_ideas": payload.get("campaign_ideas") or [],
                "content_format_recommendation": payload.get("content_format_recommendation") or {},
                "growth_hacks": payload.get("growth_hacks") or [],
                "hashtag_pack": {"primary": primary, "secondary": secondary, "niche": niche_tags},
                "model_version": getattr(self.llm, "model", None),
                "error_message": None,
            }

            await TrendAIAnalysisModel.find_one({"_id": placeholder.id}).update({"$set": update})

            emit_event(
                "trends.ai_analysis.completed",
                trend_id=trend_id,
                user_id=user_id,
                status="completed",
                model=str(getattr(self.llm, "model", "") or ""),
            )

            doc = await self.get_analysis(trend_id, user_id)
            if not doc:
                raise RuntimeError("analysis_persist_failed")
            return doc

        except Exception as e:
            msg = str(e)
            logger.warning("ai_analysis_failed trend_id=%s user_id=%s err=%s", trend_id, user_id, msg, exc_info=True)

            try:
                await TrendAIAnalysisModel.find_one({"_id": placeholder.id}).update(
                    {"$set": {"status": "failed", "updated_at": datetime.utcnow(), "error_message": msg[:500]}}
                )
            except Exception:
                pass

            emit_event(
                "trends.ai_analysis.failed",
                trend_id=trend_id,
                user_id=user_id,
                status="failed",
                error=msg,
            )
            # Return the failed placeholder so status endpoints can report it.
            doc = await self.get_analysis(trend_id, user_id)
            return doc or placeholder

