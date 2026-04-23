from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from google import genai
from google.genai import types as genai_types

from infrastructure.repositories.business_repository import BusinessRepository
from infrastructure.database.models.campaign_plan_model import CampaignPlanModel
from infrastructure.database.models.campaign_planned_post_model import CampaignPlannedPostModel

logger = logging.getLogger(__name__)


class CampaignPlannerService:
    """
    Generates a brand-driven campaign plan and planned calendar posts.

    Notes:
    - Uses Brand DNA from BusinessModel (tone/theme/tagline/specialties/location).
    - Outputs strict JSON (response_mime_type = application/json).
    - Stores plan + planned posts in MongoDB.
    """

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        self.model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
        self.client = genai.Client(api_key=api_key)
        self.business_repo = BusinessRepository()

    async def _brand_context(self, user_email: str) -> Dict[str, Any]:
        business = await self.business_repo.get_by_user_id(user_email)
        if not business:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Business profile not found. Complete onboarding first.",
            )
        return {
            "business_id": str(business.id),
            "business_name": business.business_name,
            "business_type": business.business_type,
            "city": business.city,
            "country": business.country,
            "tagline": business.tagline,
            "tone_of_voice": business.tone_of_voice,
            "restaurant_theme": business.restaurant_theme,
            "brand_colors": business.brand_colors,
            "primary_color": business.primary_color,
            "secondary_color": business.secondary_color,
            "specialties": business.specialties,
        }

    def _serialize_for_json(self, obj: Any) -> Any:
        """Convert datetime objects to ISO strings for JSON serialization."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, dict):
            return {k: self._serialize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self._serialize_for_json(item) for item in obj]
        return obj

    def _build_prompt(self, *, brief: Dict[str, Any], brand: Dict[str, Any]) -> str:
        # Keep prompt short but strict; we validate/repair times server-side.
        # Serialize datetime objects for JSON compatibility
        serialized_brief = self._serialize_for_json(brief)
        serialized_brand = self._serialize_for_json(brand)
        
        start_date = brief.get("start_date")
        end_date = brief.get("end_date")
        frequency = brief.get("posting_frequency", "3_per_week")
        
        return f"""
You are a senior brand strategist and campaign planner for a RESTAURANT brand.

HARD RULES:
- This is BRAND-DRIVEN planning. Do NOT reference external trends, trend signals, or trending audio by default.
- Every post must align with the brand tone/theme/specialties.
- Output MUST be valid JSON only. No markdown. No extra text.
- Use ISO 8601 datetime strings for scheduled_time (include timezone offset if known).

CALENDAR REQUIREMENTS:
- Campaign Start: {start_date}
- Campaign End: {end_date}
- Frequency: {frequency}
- REQUIRED: You MUST generate posts for the ENTIRE duration from start to end.
- If frequency is "3_per_week", you must provide 3 unique posts for EVERY week of the campaign.
- Ensure scheduled_time is spread logically across the weeks (e.g. Mon, Wed, Fri or Tue, Thu, Sat).
- Do NOT stop after just a few days. Fill the entire duration.
{"- REFERENCE MEDIA: Consider the visual style of this media: " + brief.get("reference_media_url") if brief.get("reference_media_url") else ""}

BRAND_DNA:
{json.dumps(serialized_brand, ensure_ascii=False)}

CAMPAIGN_BRIEF:
{json.dumps(serialized_brief, ensure_ascii=False)}

OUTPUT_JSON_SCHEMA:
{{
  "campaign_name": "string",
  "objective": "string",
  "budget_guidance": {{"min": 0, "max": 0, "split_notes": "string"}},
  "strategy_notes": "string",
  "posts": [
    {{
      "title": "string (short, calendar-friendly)",
      "post_type": "static|carousel|reel|story",
      "scheduled_time": "ISO datetime string",
      "caption_prompt": "string",
      "creative_prompt": "string",
      "cta": "string",
      "hashtags": ["#tag1", "#tag2"],
      "why_it_fits_brand": "string"
    }}
  ]
}}
""".strip()

    def _clean_json(self, s: str) -> Dict[str, Any]:
        text = (s or "").strip()
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*", "", text).strip()
            text = text[:-3].strip() if text.endswith("```") else text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", text)
            if not m:
                raise
            return json.loads(m.group(0))

    def _parse_dt_utc(self, value: Any, *, fallback_tz: str) -> datetime:
        """
        Parse a datetime-like string and normalize to UTC.
        For now we accept:
        - ISO strings with offset or Z
        - ISO strings without tz: treat as UTC (safe default)
        """
        if isinstance(value, datetime):
            dt = value
        else:
            s = str(value or "").strip()
            if not s:
                raise ValueError("missing scheduled_time")
            s = s.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # Safe default; frontend will pass explicit tz later
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    async def create_plan(self, *, user_email: str, brief: Dict[str, Any]) -> CampaignPlanModel:
        brand = await self._brand_context(user_email)
        business_id = brand["business_id"]

        # Normalize brief datetime fields
        plan = CampaignPlanModel(
            user_email=user_email,
            business_id=business_id,
            input_brief=brief,
            generated={},
            start_date=brief["start_date"],
            end_date=brief["end_date"],
            timezone=brief.get("timezone") or "UTC",
            posting_frequency=brief.get("posting_frequency") or "3_per_week",
            reference_media_url=brief.get("reference_media_url"),
            generation_status="running",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        await plan.insert()

        try:
            prompt = self._build_prompt(brief=brief, brand=brand)
            response = await self._call_llm(prompt)
            payload = self._clean_json(response)
        except Exception as e:
            logger.exception("Campaign plan generation failed: user=%s plan_id=%s", user_email, str(plan.id))
            plan.generation_status = "failed"
            plan.generation_error = str(e)[:400]
            plan.updated_at = datetime.utcnow()
            await plan.save()
            # Surface a short reason in dev to avoid "mystery failures"
            raise HTTPException(
                status_code=500,
                detail=f"Campaign plan generation failed: {plan.generation_error}",
            ) from e

        plan.generated = {
            "campaign_name": payload.get("campaign_name"),
            "objective": payload.get("objective"),
            "budget_guidance": payload.get("budget_guidance") or {},
            "strategy_notes": payload.get("strategy_notes"),
        }
        plan.generation_status = "completed"
        plan.generation_error = None
        plan.updated_at = datetime.utcnow()
        await plan.save()

        # Create planned posts - use bulk insert for better performance
        posts = payload.get("posts") or []
        docs_to_insert: List[CampaignPlannedPostModel] = []
        
        for p in posts:
            try:
                scheduled_utc = self._parse_dt_utc(p.get("scheduled_time"), fallback_tz=plan.timezone)
                doc = CampaignPlannedPostModel(
                    user_email=user_email,
                    campaign_plan_id=str(plan.id),
                    scheduled_time=scheduled_utc,
                    timezone=plan.timezone,
                    title=str(p.get("title") or "Planned post").strip()[:120],
                    post_type=(p.get("post_type") or "static"),
                    prompts={
                        "caption_prompt": p.get("caption_prompt"),
                        "creative_prompt": p.get("creative_prompt"),
                    },
                    cta=p.get("cta"),
                    hashtags=list(p.get("hashtags") or []),
                    why_it_fits_brand=p.get("why_it_fits_brand"),
                    status="planned",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                docs_to_insert.append(doc)
            except Exception as e:
                # Escape hatch: persist a failed planned post instead of losing it.
                doc = CampaignPlannedPostModel(
                    user_email=user_email,
                    campaign_plan_id=str(plan.id),
                    scheduled_time=datetime.now(timezone.utc),
                    timezone=plan.timezone,
                    title=str(p.get("title") or "Invalid planned post").strip()[:120],
                    post_type=(p.get("post_type") or "static"),
                    prompts={
                        "caption_prompt": p.get("caption_prompt"),
                        "creative_prompt": p.get("creative_prompt"),
                    },
                    cta=p.get("cta"),
                    hashtags=list(p.get("hashtags") or []),
                    why_it_fits_brand=p.get("why_it_fits_brand"),
                    status="failed",
                    last_error=f"Validation error: {str(e)[:300]}",
                    last_error_at=datetime.utcnow(),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                docs_to_insert.append(doc)

        # Bulk insert all posts in one operation
        saved: List[CampaignPlannedPostModel] = []
        if docs_to_insert:
            saved = await CampaignPlannedPostModel.insert_many(docs_to_insert)

        logger.info("Campaign plan created: user=%s plan_id=%s posts=%d", user_email, str(plan.id), len(saved))
        return plan

    async def _call_llm(self, prompt: str) -> str:
        # Run LLM call in thread to avoid blocking event loop.
        import asyncio

        timeout_s = float(os.getenv("CAMPAIGN_PLANNER_LLM_TIMEOUT_S", "35"))
        try:
            resp = await asyncio.wait_for(
                asyncio.to_thread(
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=prompt,
                        config=genai_types.GenerateContentConfig(
                            temperature=0.6,
                            # Increased for complex campaigns with many posts
                            max_output_tokens=4096,
                            response_mime_type="application/json",
                        ),
                    )
                ),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"LLM timeout after {timeout_s:.0f}s") from e
        return (resp.text or "").strip()

