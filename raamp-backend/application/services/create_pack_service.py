from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from application.use_cases.content_generation_use_case import ContentGenerationUseCase
from infrastructure.database.models.campaign_draft_model import CampaignDraftModel


class CreatePackService:
    """
    Generates a Carousel+Reel+Story pack and persists them as CampaignDraftModel rows.

    Implementation detail:
    - Uses the existing non-streaming content generation use case.
    - Tests can inject a fake ContentGenerationUseCase.
    """

    def __init__(self, content_use_case: Optional[ContentGenerationUseCase] = None):
        self.content_use_case = content_use_case or ContentGenerationUseCase()

    async def _generate_one(
        self,
        *,
        user_id: str,
        platform_type: str,
        campaign_idea: str,
    ) -> Dict[str, Any]:
        # Delegate to existing use case (handles brand context + credits + AI service)
        return await self.content_use_case.generate_social_content(
            user_id=user_id,
            campaign_idea=campaign_idea,
            platform_type=platform_type,
            content_type="all",
        )

    async def create_pack(
        self,
        *,
        user_id: str,
        trend_keyword: str,
        niche: str,
        location: str,
        suggested_hashtags: Optional[List[str]] = None,
        suggested_caption: Optional[str] = None,
        platform: Optional[str] = None,
    ) -> List[CampaignDraftModel]:
        suggested_hashtags = suggested_hashtags or []

        # One campaign idea shared across all formats, but with format hints.
        base = f'Trend: "{trend_keyword}". Business niche: {niche}. Location: {location}.'
        if platform:
            base += f" Platform: {platform}."
        if suggested_caption:
            base += f' Suggested caption seed: "{suggested_caption}".'
        if suggested_hashtags:
            base += f" Suggested hashtags: {', '.join(suggested_hashtags[:20])}."

        ideas = {
            "carousel": base
            + " Create a carousel concept (5-7 slides) with slide-by-slide copy and a strong CTA.",
            "reel": base
            + " Create a reel concept with a hook, on-screen text beats, and caption + hashtags.",
            "story": base
            + " Create a story sequence (3 frames) with interactive elements (poll/question) and CTA.",
        }

        now = datetime.utcnow()

        # Generate three packs
        carousel_res = await self._generate_one(user_id=user_id, platform_type="post", campaign_idea=ideas["carousel"])
        reel_res = await self._generate_one(user_id=user_id, platform_type="reel", campaign_idea=ideas["reel"])
        story_res = await self._generate_one(user_id=user_id, platform_type="story", campaign_idea=ideas["story"])

        def pick_best_payload(res: Dict[str, Any]) -> Dict[str, Any]:
            # Keep a compact payload: best caption + hashtags + full variants for power users.
            caption_variants = res.get("caption_variants") or []
            best_id = res.get("best_caption_id")
            best = None
            for v in caption_variants:
                if v.get("id") == best_id:
                    best = v
                    break
            if not best and caption_variants:
                best = caption_variants[0]
            return {
                "best_caption": best.get("caption") if isinstance(best, dict) else None,
                "best_hashtags": best.get("hashtags") if isinstance(best, dict) else [],
                "caption_variants": caption_variants,
                "hashtag_sets": res.get("hashtag_sets") or [],
                "platform_type": res.get("platform_type"),
                "generated_at": res.get("generated_at"),
            }

        drafts = [
            CampaignDraftModel(
                user_id=user_id,
                kind="carousel",
                trend_keyword=trend_keyword,
                niche=niche,
                location=location,
                title=f'Carousel pack • {trend_keyword}',
                content=pick_best_payload(carousel_res),
                created_at=now,
                updated_at=now,
            ),
            CampaignDraftModel(
                user_id=user_id,
                kind="reel",
                trend_keyword=trend_keyword,
                niche=niche,
                location=location,
                title=f'Reel pack • {trend_keyword}',
                content=pick_best_payload(reel_res),
                created_at=now,
                updated_at=now,
            ),
            CampaignDraftModel(
                user_id=user_id,
                kind="story",
                trend_keyword=trend_keyword,
                niche=niche,
                location=location,
                title=f'Story pack • {trend_keyword}',
                content=pick_best_payload(story_res),
                created_at=now,
                updated_at=now,
            ),
        ]

        # Persist
        saved = []
        for d in drafts:
            saved.append(await d.insert())
        return saved

