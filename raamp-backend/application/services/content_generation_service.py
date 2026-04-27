"""
Content Generation Service
==========================
AI-powered service for generating ALL social media content types in one call.
Generates: Captions, Hashtags, WhatsApp/Email messages, and AI-generated images.
Uses Google GenAI SDK directly for maximum model compatibility.
"""

import os
import json
import re
import logging
import asyncio
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from google import genai
from google.genai import types as genai_types
from dotenv import load_dotenv

# Import image generation service
from application.services.image_generation_service import get_image_generation_service

# Import caption logging
from infrastructure.repositories.caption_log_repository import CaptionLogRepository
from infrastructure.database.models.caption_log_model import AssetTypeEnum

# Import industry templates
from application.services.industry_templates import build_industry_prompt_injection, infer_business_domain

# Import business type enum
from infrastructure.database.models.business_model import BusinessTypeEnum

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """
    Service for generating AI-powered social media content.
    
    Generates ALL content types in a single request:
    - Social media captions + hashtags (3 variants)
    - Standalone hashtag sets (3 sets)
    - WhatsApp/Email campaign messages (3 variants)
    - Image generation prompts (coming soon)
    
    Supports multiple platform types:
    - Post: Regular Instagram/Facebook posts
    - Story: Instagram Stories (9:16, interactive elements)
    - Reel: Instagram Reels (short-form, trending audio)
    """
    
    # System prompt for regular posts (default)
    SYSTEM_PROMPT_POST = """You are an elite social media director. Generate a COMPLETE marketing package for Instagram/Facebook POSTS.
      
    OUTPUT REQUIREMENTS:
    1. Three distinct caption variants with hashtags (Vibrant, Informative, Playful)
    2. Three standalone hashtag sets (Broad, Niche, Mixed)
    3. Three WhatsApp/Email variants (Professional, Friendly, Urgent)
    4. Three Image generation prompts
    
    CONSTRAINTS:
    - Captions MUST be short, catchy, fun, and engaging. Maximum 2-4 lines.
    - Caption format MUST strictly follow: 
      [Hook Line]
      [1-2 short supporting lines with optional emoji]
      [Call to Action]
    - Generate content aligned with the brand's tone, audience, and industry.
    - Ensure the output feels natural for the business and matches its marketing style.
    
    INDUSTRY-SPECIFIC LANGUAGE RULES:
    - For RESTAURANTS/FOOD businesses: Use appetizing, sensory language (crispy, juicy, aromatic, fresh, savory, delicious). Focus on dining experience, flavors, and dishes. Say "dish/meal/menu item" NOT "product/service/offering".
      STRICT RULE: The words "product", "service", "offering" are FORBIDDEN. Using them makes the output INVALID. Use "dish", "meal", "specialty" instead.
    - For FASHION businesses: Use style-focused language (trendy, chic, elegant, bold). Focus on looks, outfits, and personal expression.
    - For TECH businesses: Use innovation language (cutting-edge, seamless, powerful). Focus on features, benefits, and user experience.
    - For HEALTHCARE/WELLNESS: Use empowering language (transform, energize, revitalize). Focus on well-being and positive outcomes.
    
    - JSON format only. No preamble.
"""

    # System prompt for Instagram Stories
    SYSTEM_PROMPT_STORY = """You are an expert in Instagram STORIES. Generate content for 9:16 vertical format in JSON.
    
    OUTPUT REQUIREMENTS:
    1. Three punchy story overlay captions (MAX 50 characters each)
    2. Three small hashtag sets (3-5 tags each)
    3. Three WhatsApp message variants
    4. Three vertical image prompts (9:16)
    
    CONSTRAINTS:
    - Suggest ONE specific interactive sticker (Poll, Quiz, etc.) for each story variant.
    - JSON format only. No preamble.
    """

    SYSTEM_PROMPT_REEL = """You are a viral REEL strategist. Generate content optimized for current trending audio and hooks in JSON.
    
    OUTPUT REQUIREMENTS:
    1. Three high-hook Reel captions with video concepts
    2. Three hashtag sets (trending focused)
    3. Three WhatsApp message variants
    4. Three Reel-specific image/video prompts
    
    CONSTRAINTS:
    - Focus on curiosity hooks and pattern interrupts.
    - JSON format only. No preamble.
    """
    def __init__(self):
        """Initialize the content generation service using Google GenAI SDK."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            logger.error("GEMINI_API_KEY environment variable is not set")
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        logger.info("🔑 Initializing ContentGenerationService with Google GenAI SDK...")
        
        try:
            self.model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
            self.client = genai.Client(api_key=self.api_key)
            
            # Initialize caption log repository
            self.caption_repo = CaptionLogRepository()
            
            logger.info(f"✅ ContentGenerationService initialized with: {self.model}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize GenAI client: {e}")
            raise
    
    def _get_system_prompt(self, platform_type: str) -> str:
        """Get the appropriate system prompt based on platform type."""
        prompts = {
            "post": self.SYSTEM_PROMPT_POST,
            "story": self.SYSTEM_PROMPT_STORY,
            "reel": self.SYSTEM_PROMPT_REEL
        }
        return prompts.get(platform_type.lower(), self.SYSTEM_PROMPT_POST)
    
    def _build_brand_context_prompt(self, brand_context: Dict[str, Any]) -> str:
        """Build the brand context section of the prompt with restaurant-specific awareness."""
        sections = []
        
        # Core business identity
        if brand_context.get("business_name"):
            sections.append(f"Business Name: {brand_context['business_name']}")
        
        if brand_context.get("tagline"):
            sections.append(f"Brand Tagline: {brand_context['tagline']}")
        
        if brand_context.get("tone_of_voice"):
            sections.append(f"Default Brand Tone: {brand_context['tone_of_voice']}")
        
        if brand_context.get("restaurant_theme"):
            sections.append(f"Brand Theme/Ambiance: {brand_context['restaurant_theme']}")
        
        # Restaurant-specific context
        if brand_context.get("business_type"):
            sections.append(f"Business Type: {brand_context['business_type']}")
        
        if brand_context.get("specialties"):
            specialties_list = brand_context['specialties']
            if isinstance(specialties_list, list) and specialties_list:
                sections.append(f"Cuisine/Specialties: {', '.join(specialties_list)}")
        
        if brand_context.get("city") and brand_context.get("country"):
            sections.append(f"Location: {brand_context['city']}, {brand_context['country']}")
        elif brand_context.get("city"):
            sections.append(f"Location: {brand_context['city']}")
        elif brand_context.get("country"):
            sections.append(f"Location: {brand_context['country']}")
        
        # Visual brand identity
        palette: list[str] = []
        if brand_context.get("brand_colors"):
            try:
                palette = [str(c).strip() for c in (brand_context.get("brand_colors") or []) if str(c).strip()]
            except Exception:
                palette = []
        if not palette and (brand_context.get("primary_color") or brand_context.get("secondary_color")):
            if brand_context.get("primary_color"):
                palette.append(str(brand_context["primary_color"]).strip())
            if brand_context.get("secondary_color"):
                palette.append(str(brand_context["secondary_color"]).strip())
        if palette:
            sections.append(f"Brand Color Palette (HEX): {', '.join(palette[:6])}")
        
        if brand_context.get("brand_logo_url"):
            sections.append(f"Brand Logo: {brand_context['brand_logo_url']} (incorporate visual brand identity into image prompts)")
        
        if not sections:
            return (
                "BRAND CONSTRAINTS:\n"
                "- No brand information is available. You may generate generic but professional content.\n"
                "- IMPORTANT: Still avoid bland/generic filler; be specific to the campaign idea."
            )

        # Build constraints with restaurant-specific rules
        biz_name = brand_context.get("business_name")
        tagline = brand_context.get("tagline")
        tone = brand_context.get("tone_of_voice")
        business_type = brand_context.get("business_type", "").lower()
        specialties = brand_context.get("specialties", [])
        city = brand_context.get("city")
        
        # Detect if this is a restaurant/food business using BusinessTypeEnum
        is_restaurant = business_type in [
            BusinessTypeEnum.RESTAURANT.value,
            BusinessTypeEnum.CAFE.value,
            BusinessTypeEnum.BAKERY.value,
        ]
        
        constraints: list[str] = [
            "BRAND CONSTRAINTS (HARD RULES — treat violations as INVALID output):",
        ]
        
        # Restaurant-specific instructions
        if is_restaurant:
            constraints.append("⚠️ RESTAURANT CONTENT RULES:")
            constraints.append("- This is a RESTAURANT/FOOD business. Use food/dining language throughout.")
            constraints.append("- Make content APPETIZING: describe flavors, textures, aromas, dining experiences.")
            constraints.append("- Use sensory words: 'crispy', 'juicy', 'aromatic', 'fresh', 'savory', 'delicious'.")
            constraints.append("- Focus on the DINING EXPERIENCE, not just products.")
            
            if specialties:
                constraints.append(f"- Emphasize cuisine specialties: {', '.join(specialties)}.")
                constraints.append(f"- Use cuisine-specific terminology relevant to {', '.join(specialties)}.")
            
            if city:
                constraints.append(f"- Reference local food culture and preferences in {city} where appropriate.")
                constraints.append(f"- Use location-aware language: 'in {city}', 'local favorite', 'neighborhood gem'.")
            
            constraints.append("- Avoid generic business language like 'product', 'service', 'offering'.")
            constraints.append("- Instead use: 'dish', 'meal', 'menu item', 'specialty', 'recipe', 'dining experience'.")
            constraints.append("")
        
        # Standard brand constraints
        if biz_name:
            constraints.append(f'- Business name MUST appear verbatim in EVERY caption variant: "{biz_name}".')
        if tagline:
            constraints.append(f'- Tagline MUST be incorporated verbatim (do not paraphrase): "{tagline}".')
        if tone:
            constraints.append(f'- Tone MUST be followed strictly: "{tone}".')
        if palette:
            constraints.append(
                "- Visual direction MUST use the brand palette. "
                f"Every image prompt MUST explicitly mention these HEX colors: {', '.join(palette[:6])}. "
                "Avoid introducing unrelated brand colors (except black/white/neutral grays)."
            )
        if brand_context.get("brand_logo_url"):
            constraints.append(
                "- Image prompts MUST incorporate the brand logo identity cues (logo placement, end-card, watermark, or typography cues)."
            )
        constraints.extend([
            "- Do NOT produce generic content. Every line must reflect the specific campaign idea.",
            "- If a brand field is missing, do NOT invent one; use only what is provided.",
            "",
            "BRAND VOICE GUIDELINES (context):",
            *[f"• {s}" for s in sections],
        ])
        return "\n".join(constraints)
    
    def _build_user_prompt(
        self,
        campaign_idea: str,
        target_audience: Optional[str],
        campaign_tone: Optional[str],
        brand_context: Dict[str, Any],
        platform_type: str = "post",
        content_type: str = "all"
    ) -> str:
        """Build the complete user prompt for unified content generation."""
        
        # Brand context section
        brand_section = self._build_brand_context_prompt(brand_context)
        
        # Industry-specific optimization context
        industry_section = ""
        business_type = brand_context.get("business_type")
        
        # Infer business domain from business_type if not explicitly provided
        business_domain = brand_context.get("business_domain")
        if not business_domain and business_type:
            business_domain = infer_business_domain(business_type)
            logger.info(f"Inferred business domain '{business_domain}' from business type '{business_type}'")
        
        if business_domain:
            try:
                industry_section = build_industry_prompt_injection(
                    business_domain=business_domain,
                    business_type=business_type,
                    tone_modifier=None  # Could be extended later
                )
            except Exception as e:
                logger.warning(f"Failed to build industry context: {e}")
                industry_section = ""
        
        # Build the prompt (put constraints first so the model treats them as primary).
        biz_name = brand_context.get("business_name", "Our Team")
        prompt_parts = [brand_section, ""]
        
        # Add industry-specific section if available
        if industry_section:
            prompt_parts.extend([
                industry_section,
                ""
            ])
        
        prompt_parts.extend([
            "CAMPAIGN DETAILS:",
            f"Campaign Idea: {campaign_idea}"
        ])
        
        if target_audience:
            prompt_parts.append(f"Target Audience: {target_audience}")
        
        if campaign_tone:
            prompt_parts.append(f"Campaign Tone Override: {campaign_tone} (prioritize this tone while keeping brand voice)")
        elif brand_context.get("tone_of_voice"):
            prompt_parts.append(f"Using Default Brand Tone: {brand_context['tone_of_voice']}")
        
        prompt_parts.extend([
            "",
            "TASK: Generate a COMPLETE marketing package following the EXACT JSON schema below.",
            "CONTENT GUIDELINES:",
            "1. Three social media captions: short, catchy (2-4 lines max), brand-aligned, ending with exactly 5-8 hashtags.",
            "2. Three hashtag strategy sets (Reach, Niche, Local).",
            "3. WhatsApp Messages: SHORT, CASUAL, CHATTY. NO Subject lines. NO placeholders. Start with 'Hey {{name}}!'. End with a friendly sign-off like 'Regards, Team {biz_name}'.",
            f"4. Email Campaigns: PROFESSIONAL, STRUCTURED. Format EXACTLY as:\n   Subject: [Compelling Line]\n   Body: [Professional greeting, 2 paragraphs of detail]\n   Regards,\n   Team {biz_name}",
            "5. Three detailed, descriptive image prompts. Follow the CAMPAIGN IDEA's visual theme primarily (brand identity should be integrated, not replace the campaign theme).",
            "",
            "EXACT JSON SCHEMA TO FOLLOW:",
            "{",
            '  "caption_variants": [',
            '    { "id": 1, "tone": "Professional", "caption": "your short caption text here", "hashtags": ["#tag1", "#tag2", ...] },',
            "    ...",
            "  ],",
            '  "hashtag_sets": [',
            '    { "id": 1, "strategy": "Reach", "hashtags": ["#tag1", "#tag2", ...] },',
            "    ...",
            "  ],",
            '  "whatsapp_variants": [',
            '    { "id": 1, "tone": "Friendly", "message": "Hey {{name}}! Check out our new campaign...", "predicted_performance": "High" },',
            "    ...",
            "  ],",
            '  "email_variants": [',
            '    { "id": 1, "tone": "Professional", "message": "Subject: [Topic]\\n\\nBody: [Details]\\n\\nRegards, [Team]", "predicted_performance": "High" },',
            "    ...",
            "  ],",
            '  "image_prompts": [',
            '    "detailed image prompt 1",',
            '    "detailed image prompt 2",',
            '    "detailed image prompt 3"',
            "  ]",
            "}",
            "",
            "IMPORTANT: Output ONLY the JSON block. Do not include any conversational text."
        ])
        
        return "\n".join(prompt_parts)
    
    async def generate_content(
        self,
        campaign_idea: str,
        brand_context: Dict[str, Any],
        user_id: str,
        target_audience: Optional[str] = None,
        campaign_tone: Optional[str] = None,
        platform_type: str = "post",
        campaign_id: Optional[str] = None,
        content_type: str = "all",
        aspect_ratio: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate ALL content types in a single AI call.
        
        Args:
            campaign_idea: The campaign vision/idea from user
            brand_context: Brand information from database
            user_id: User identifier for asset ownership
            target_audience: Optional target audience description
            campaign_tone: Optional tone override for this campaign
            platform_type: Content platform (post, story, reel) - defaults to "post"
            campaign_id: Optional campaign identifier for grouping
            
        Returns:
            Dictionary with all content types and metadata
        """
        try:
            logger.info(f"🚀 Starting content generation for user: {user_id}")
            logger.info(f"📱 Platform type: {platform_type}")
            logger.info(f"� Content type: {content_type}")
            logger.info(f"📝 Campaign idea: {campaign_idea[:100]}...")
            logger.info(f"👥 Target audience: {target_audience}")
            logger.info(f"🎭 Campaign tone: {campaign_tone}")
            
            # Normalise content_type
            content_type = (content_type or "all").lower().strip()
            
            # Build the user prompt
            # Enrich brand context with more details if available
            biz_name = brand_context.get("business_name") or brand_context.get("name") or "our brand"
            brand_context["business_name"] = biz_name # Ensure consistency
            
            user_prompt = self._build_user_prompt(
                campaign_idea=campaign_idea,
                brand_context=brand_context,
                target_audience=target_audience,
                campaign_tone=campaign_tone,
                platform_type=platform_type,
                content_type=content_type
            )
            
            # Append per-type instruction so the LLM focuses where needed
            if content_type == "emails":
                user_prompt += (
                    "\n\n⚠️ IMPORTANT INSTRUCTION: The message_variants MUST be formatted as "
                    "PROFESSIONAL EMAIL CAMPAIGNS. Each variant must include: "
                    "a compelling subject line (prefix with 'Subject: '), a personalised greeting, "
                    "well-structured body paragraphs (2-3 short paragraphs), a clear CTA, "
                    "and a professional sign-off. Do NOT write these as WhatsApp messages."
                )
            elif content_type == "whatsapp":
                user_prompt += (
                    "\n\n⚠️ IMPORTANT INSTRUCTION: The message_variants MUST be short, "
                    "conversational WHATSAPP BROADCAST MESSAGES. Keep each under 200 words, "
                    "use emojis for tone, start with a friendly greeting, include a clear offer "
                    "or CTA, and end with a direct action link or instruction."
                )
            
            # ----- Brand-lock validation + bounded retries -----
            def _norm(s: Optional[str]) -> str:
                return (s or "").strip().lower()

            biz_name_req = (brand_context.get("business_name") or "").strip()
            tagline_req = (brand_context.get("tagline") or "").strip()

            def _ensure_verbatim_line(text: str, *, required: str) -> str:
                """
                Ensure `required` appears in `text` verbatim (case-sensitive substring).
                If missing, append as a new line while staying under Instagram caption limits.
                """
                if not required:
                    return str(text or "").strip()
                base = str(text or "").strip()
                if required in base:
                    return base
                limit = 2200
                addition = ("\n" if base else "") + required
                if len(base) + len(addition) <= limit:
                    return base + addition
                keep = max(0, limit - len(addition))
                truncated = base[:keep].rstrip()
                return truncated + addition

            def _tagline_probe(tagline: str) -> str:
                words = [w for w in re.split(r"\s+", tagline.strip()) if w]
                if len(words) >= 10:
                    return " ".join(words[:5])
                return tagline.strip()

            tagline_probe = _tagline_probe(tagline_req) if tagline_req else ""

            def _validate_brand_lock(
                *,
                captions: list[dict],
                whatsapp: list[dict],
                emails: list[dict],
                ct: str,
            ) -> list[dict]:
                warnings: list[dict] = []
                biz_norm = _norm(biz_name_req)
                tag_norm = _norm(tagline_probe)

                def check_variants(label: str, variants: list[dict], text_key: str):
                    if not variants:
                        return
                    tag_found_any = False
                    for v in variants[:3]:
                        vid = v.get("id")
                        text = str(v.get(text_key, "") or "")
                        text_norm = _norm(text)
                        missing = []
                        if biz_norm and biz_norm not in text_norm:
                            missing.append("business_name")
                        if tag_norm and tag_norm in text_norm:
                            tag_found_any = True
                        if missing:
                            warnings.append(
                                {
                                    "type": "brand_lock",
                                    "content_type": label,
                                    "variant_id": vid,
                                    "missing": missing,
                                }
                            )
                    if tag_norm and not tag_found_any:
                        warnings.append(
                            {
                                "type": "brand_lock",
                                "content_type": label,
                                "variant_id": None,
                                "missing": ["tagline"],
                                "detail": "Tagline not found in any variant for this content type.",
                            }
                        )

                # Only validate types that are actually expected for this request.
                if ct in ("all", "captions"):
                    check_variants("captions", captions, "caption")
                if ct in ("all", "whatsapp"):
                    check_variants("whatsapp", whatsapp, "message")
                if ct in ("all", "emails"):
                    check_variants("emails", emails, "message")
                return warnings

            def _build_retry_prefix(warnings: list[dict], attempt: int) -> str:
                if not warnings:
                    return ""
                lines = [
                    "VALIDATION FAILURE FROM PREVIOUS GENERATION (MUST FIX):",
                    "The previous output violated BRAND CONSTRAINTS. Regenerate and ensure all requirements are met.",
                ]
                # Mention a few concrete failures for targeting.
                for w in warnings[:6]:
                    ct = w.get("content_type")
                    vid = w.get("variant_id")
                    missing = ", ".join(w.get("missing", []))
                    lines.append(f"- {ct} variant {vid}: missing {missing}.")
                if attempt >= 1:
                    lines.append("SECOND ATTEMPT: This is your final chance. Output MUST pass all brand constraints.")
                lines.append("")
                return "\n".join(lines)

            # retry loop (0 + up to 2 retries = 3 total attempts)
            max_retries = 2
            validation_warnings: list[dict] = []
            logo_used = None
            logo_warning = None
            result = None

            for attempt in range(0, max_retries + 1):
                # Select appropriate system prompt based on platform type
                system_prompt = self._get_system_prompt(platform_type)
                retry_prefix = _build_retry_prefix(validation_warnings, attempt) if attempt > 0 else ""
                full_prompt = f"{retry_prefix}{system_prompt}\n\n{user_prompt}"
                logger.info(
                    "📤 Calling GenAI SDK — model: %s, platform: %s, content_type: %s, attempt: %d/%d",
                    self.model,
                    platform_type,
                    content_type,
                    attempt + 1,
                    max_retries + 1,
                )

                try:
                    response = await asyncio.to_thread(
                        lambda: self.client.models.generate_content(
                            model=self.model,
                            contents=full_prompt,
                            config=genai_types.GenerateContentConfig(
                                temperature=0.8,
                                max_output_tokens=4096,
                                response_mime_type="application/json",
                            ),
                        )
                    )
                    raw_text = response.text
                except Exception as api_error:
                    logger.error("❌ GenAI SDK call failed: %s: %s", type(api_error).__name__, api_error)
                    error_msg = str(api_error).lower()
                    if "quota" in error_msg or "429" in error_msg:
                        detail = "API quota exhausted. Please check your billing."
                    elif "401" in error_msg or "api_key" in error_msg:
                        detail = "Invalid Gemini API key. Please check your .env configuration."
                    elif "404" in error_msg or "not found" in error_msg:
                        detail = f"Model '{self.model}' is not accessible with your API key tier."
                    else:
                        detail = f"Technical error: {str(api_error)[:200]}"
                    return {"success": False, "error": "AI service temporarily unavailable", "detail": detail}

                content = (raw_text or "").strip()
                # Clean response content (remove markdown code blocks if present)
                if content.startswith("```json"):
                    content = content.replace("```json", "", 1)
                    if content.endswith("```"):
                        content = content[:-3]
                elif content.startswith("```"):
                    content = content.replace("```", "", 1)
                    if content.endswith("```"):
                        content = content[:-3]
                content = content.strip()

                # Extract JSON — try raw first, then regex search for first {...} block
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    match = re.search(r"\{[\s\S]*\}", content)
                    if match:
                        result = json.loads(match.group(0))
                    else:
                        raise json.JSONDecodeError("No JSON block found", content, 0)

                # Pre-normalization brand-lock validation. If it fails, retry generation.
                # (We validate again after normalization only to attach warnings in the final response.)
                def _raw_variants(key: str, text_key: str) -> list[dict]:
                    items = result.get(key, []) or []
                    if isinstance(items, dict):
                        items = list(items.values())
                    if not isinstance(items, list):
                        return []
                    out: list[dict] = []
                    for i, it in enumerate(items[:3]):
                        if isinstance(it, dict):
                            out.append({"id": it.get("id", i + 1), text_key: it.get(text_key, "")})
                    return out

                raw_captions = _raw_variants("caption_variants", "caption")
                raw_whatsapp = _raw_variants("whatsapp_variants", "message") or _raw_variants("message_variants", "message")
                raw_emails = _raw_variants("email_variants", "message")

                validation_warnings = _validate_brand_lock(
                    captions=raw_captions,
                    whatsapp=raw_whatsapp,
                    emails=raw_emails,
                    ct=content_type,
                )

                if validation_warnings and attempt < max_retries:
                    logger.warning(
                        "⚠️ Brand-lock validation failed (attempt %d/%d). Retrying generation.",
                        attempt + 1,
                        max_retries + 1,
                    )
                    continue

                # Either validation passed, or we're out of retries; proceed to normalization.
                break
            
            # Validate and normalize caption variants
            caption_variants = result.get("caption_variants", [])
            
            # Handle case where AI returns a dict instead of a list (common with GPT-4o-mini JSON mode)
            if isinstance(caption_variants, dict):
                logger.warning("⚠️ AI returned caption_variants as a dict, converting to list")
                caption_variants = list(caption_variants.values())
            
            if not caption_variants or not isinstance(caption_variants, list) or len(caption_variants) < 3:
                # Fallback if not enough variants
                if not isinstance(caption_variants, list):
                    caption_variants = []
                while len(caption_variants) < 3:
                    caption_variants.append({
                        "id": len(caption_variants) + 1,
                        "tone": f"Variant {len(caption_variants) + 1}",
                        "caption": "Content generation in progress...",
                        "hashtags": ["#Brand", "#Marketing"],
                        "predicted_performance": "Good"
                    })
            
            # Generate caption_ids first
            caption_ids = [str(uuid.uuid4()) for _ in range(min(3, len(caption_variants)))]
            
            normalized_captions = []
            for i, variant in enumerate(caption_variants[:3]):
                caption_id = caption_ids[i] if i < len(caption_ids) else str(uuid.uuid4())
                hashtags = variant.get("hashtags", [])
                if not isinstance(hashtags, list):
                    hashtags = [hashtags] if hashtags else []
                
                # Post-processing: Enforce at least 5 hashtags
                if len(hashtags) < 5:
                    defaults = ["#Brand", "#Marketing", "#Viral", "#Trending", f"#{platform_type}"]
                    while len(hashtags) < 5:
                        hashtags.append(defaults[len(hashtags) % len(defaults)])

                caption_text = variant.get("caption", "")
                if tagline_req:
                    caption_text = _ensure_verbatim_line(caption_text, required=tagline_req)

                normalized_captions.append({
                    "id": variant.get("id", i + 1),
                    "caption_id": caption_id,  # Add caption_id to variant
                    "tone": variant.get("tone", f"Variant {i + 1}"),
                    "caption": caption_text,
                    "hashtags": hashtags,
                    "predicted_performance": variant.get("predicted_performance", "Good")
                })
            
            # ── ML ENRICHMENT ─────────────────────────────────────────────────────────
            # Replace hardcoded "Good" scores with ML-predicted engagement rates.
            # Graceful: if models aren't trained yet, variants pass through unchanged.
            try:
                from application.services.ml_enrichment_service import enrich_captions
                normalized_captions, ml_best_id = await enrich_captions(
                    variants=normalized_captions,
                    tone=campaign_tone or brand_context.get("tone_of_voice", "General"),
                    asset_type=platform_type,
                )
                logger.info("✅ ML enrichment applied — best_caption_id=%s", ml_best_id)
            except Exception as ml_err:
                ml_best_id = result.get("best_caption_id", 1)
                logger.warning("⚠️ ML enrichment skipped: %s", ml_err)
            # ── END ML ENRICHMENT ─────────────────────────────────────────────────────

            # Define asset_type_map here so it's always in scope for caption + hashtag logging

            asset_type_map = {
                "post": AssetTypeEnum.POST,
                "story": AssetTypeEnum.STORY,
                "reel": AssetTypeEnum.REEL
            }

            # Log captions to database (non-blocking)
            try:
                # Map platform_type to AssetTypeEnum
                asset_type = asset_type_map.get(platform_type.lower(), AssetTypeEnum.POST)
                
                # Prepare caption logs for bulk insert
                caption_logs_data = []
                for caption_data in normalized_captions:
                    caption_log = {
                        "caption_id": caption_data["caption_id"],  # Use existing caption_id
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "campaign_idea": campaign_idea[:500] if campaign_idea else None,  # Truncate long ideas
                        "asset_type": asset_type,
                        "caption_text": caption_data["caption"],
                        "hashtags": caption_data["hashtags"],
                        "tone": caption_data["tone"],
                        "generation_prompt": user_prompt[:1000] if user_prompt else None,  # Store first 1000 chars
                        "model_used": self.model,
                        "variant_number": caption_data["id"],
                        "predicted_performance": caption_data.get("predicted_performance"),
                        "brand_tone_used": brand_context.get("tone_of_voice"),
                        "target_audience": target_audience,
                        "times_used": 0,
                        "tags": [platform_type, campaign_tone] if campaign_tone else [platform_type],
                        "is_favorite": False
                    }
                    caption_logs_data.append(caption_log)
                
                # Bulk insert captions (don't block on failure)
                await self.caption_repo.create_many(caption_logs_data)
                logger.info(f"✅ Logged {len(caption_logs_data)} captions to database")
            except Exception as log_error:
                # Don't fail the entire request if logging fails
                logger.error(f"⚠️ Failed to log captions: {log_error}")
                logger.error(f"Logging error type: {type(log_error).__name__}")
            
            # Normalize hashtag sets
            hashtag_sets = result.get("hashtag_sets", [])
            
            # Handle case where AI returns a dict instead of a list
            if isinstance(hashtag_sets, dict):
                logger.warning("⚠️ AI returned hashtag_sets as a dict, converting to list")
                hashtag_sets = list(hashtag_sets.values())
            
            # If AI didn't return hashtag_sets in the new format but as a raw list of lists
            # handle it gracefully
            if hashtag_sets and isinstance(hashtag_sets, list) and len(hashtag_sets) > 0:
                if isinstance(hashtag_sets[0], list):
                    # It's a list of lists, convert to list of dicts
                    temp_sets = []
                    for i, h_list in enumerate(hashtag_sets):
                        temp_sets.append({
                            "id": i + 1,
                            "hashtag_id": str(uuid.uuid4()),
                            "hashtags": h_list
                        })
                    hashtag_sets = temp_sets
            
            if not hashtag_sets or not isinstance(hashtag_sets, list) or len(hashtag_sets) < 3:
                # Generate from caption hashtags as fallback
                fallback_sets = [
                    normalized_captions[0].get("hashtags", [])[:8],
                    normalized_captions[1].get("hashtags", [])[:8] if len(normalized_captions) > 1 else [],
                    normalized_captions[2].get("hashtags", [])[:8] if len(normalized_captions) > 2 else []
                ]
                hashtag_sets = []
                for i, h_list in enumerate(fallback_sets):
                    hashtag_sets.append({
                        "id": i + 1,
                        "hashtag_id": str(uuid.uuid4()),
                        "hashtags": h_list
                    })
            
            # Final normalization to ensure objects match schema
            normalized_hashtag_sets = []
            for i, h_set in enumerate(hashtag_sets[:3] if isinstance(hashtag_sets, list) else []):
                h_id = (h_set.get("hashtag_id") or str(uuid.uuid4())) if isinstance(h_set, dict) else str(uuid.uuid4())
                normalized_hashtag_sets.append({
                    "id": i + 1,
                    "hashtag_id": h_id,
                    "hashtags": h_set.get("hashtags", []) if isinstance(h_set, dict) else h_set
                })

            # Pick best hashtag set using a lightweight deterministic heuristic.
            # Goal: avoid always returning 1, while staying stable for the same inputs.
            def _score_hashtag_set(tags: Any) -> float:
                if not isinstance(tags, list):
                    return 0.0
                cleaned: list[str] = []
                for t in tags:
                    if not t:
                        continue
                    s = str(t).strip()
                    if not s:
                        continue
                    # Normalize leading '#'
                    if not s.startswith("#"):
                        s = "#" + s.lstrip("#")
                    cleaned.append(s.lower())
                if not cleaned:
                    return 0.0
                unique = list(dict.fromkeys(cleaned))
                uniq_n = len(unique)
                # Encourage variety: mix of short/broad + longer/niche tags
                lens = [len(x) for x in unique]
                short = sum(1 for l in lens if l <= 10)
                long = sum(1 for l in lens if l >= 16)
                diversity = 1.0 if (short > 0 and long > 0) else 0.0
                # Penalize duplicates
                dup_penalty = max(0, len(cleaned) - uniq_n)
                return (uniq_n * 1.0) + (diversity * 1.5) - (dup_penalty * 0.5)

            best_hashtag_set_id = 1
            try:
                if normalized_hashtag_sets:
                    scored = [
                        (float(_score_hashtag_set(s.get("hashtags"))), int(s.get("id", idx + 1)))
                        for idx, s in enumerate(normalized_hashtag_sets)
                    ]
                    # Highest score wins; tie-breaker prefers middle set (2), then 3, then 1.
                    scored.sort(key=lambda x: (x[0], {2: 3, 3: 2, 1: 1}.get(x[1], 0)), reverse=True)
                    best_hashtag_set_id = scored[0][1] if scored else 1
            except Exception as e:
                logger.warning("⚠️ Hashtag set scoring failed, defaulting to 1: %s", e)
                best_hashtag_set_id = 1
            
            # Log hashtag sets to database (non-blocking)
            try:
                hashtag_logs_data = []
                for hashtag_data in normalized_hashtag_sets:
                    hashtag_log = {
                        "caption_id": hashtag_data["hashtag_id"],  # Using caption_id field for hashtag_id
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "campaign_idea": campaign_idea[:500] if campaign_idea else None,
                        "asset_type": AssetTypeEnum.HASHTAG,
                        "caption_text": f"Hashtag Set {hashtag_data['id']}",  # Descriptive text
                        "hashtags": hashtag_data["hashtags"],
                        "tone": f"Set {hashtag_data['id']}",
                        "generation_prompt": user_prompt[:1000] if user_prompt else None,
                        "model_used": self.model,
                        "variant_number": hashtag_data["id"],
                        "predicted_performance": "Good",
                        "brand_tone_used": brand_context.get("tone_of_voice"),
                        "target_audience": target_audience,
                        "times_used": 0,
                        "tags": [platform_type, "hashtags"] + ([campaign_tone] if campaign_tone else []),
                        "is_favorite": False
                    }
                    hashtag_logs_data.append(hashtag_log)
                
                await self.caption_repo.create_many(hashtag_logs_data)
                logger.info(f"✅ Logged {len(hashtag_logs_data)} hashtag sets to database")
            except Exception as log_error:
                logger.error(f"⚠️ Failed to log hashtags: {log_error}")
            
            # Normalize WhatsApp variants
            whatsapp_variants_raw = result.get("whatsapp_variants", [])
            if not whatsapp_variants_raw:
                # Fallback to message_variants if AI didn't follow new schema
                whatsapp_variants_raw = result.get("message_variants", [])
            
            if not whatsapp_variants_raw or len(whatsapp_variants_raw) < 3:
                default_tones = ["Friendly", "Direct", "Urgent"]
                while len(whatsapp_variants_raw) < 3:
                    idx = len(whatsapp_variants_raw)
                    biz_name = brand_context.get("business_name", "Our Team")
                    msg = f"Hey {{name}}! We've got a special {campaign_idea[:30]} campaign running just for you! Check it out here: [Link] \n\nRegards, Team {biz_name}"
                    whatsapp_variants_raw.append({"id": idx + 1, "tone": default_tones[idx], "message": msg, "predicted_performance": "Good"})

            normalized_whatsapp = []
            for i, msg in enumerate(whatsapp_variants_raw[:3]):
                text = msg.get("message", "")
                text = re.sub(r'Subject:.*?\n', '', text, flags=re.IGNORECASE)
                text = re.sub(r'Body:\s*', '', text, flags=re.IGNORECASE)
                text = text.replace("[Body]", "").replace("[Subject]", "").strip()
                if "hey {name}" not in text.lower():
                    if not text.startswith("Hey"):
                        text = f"Hey {{name}}! " + text
                biz_name = brand_context.get("business_name", "Our Team")
                # Aggressive replacement of common placeholders
                text = text.replace("[Team]", biz_name).replace("[Your Team]", biz_name)
                text = text.replace("[Brand Name]", biz_name).replace("{{brand_name}}", biz_name)
                text = text.replace("Our Brand", biz_name).replace("[Brand]", biz_name)

                if "regards" not in text.lower() and "best" not in text.lower() and "cheers" not in text.lower():
                    text += f"\n\nRegards, Team {biz_name}"

                # Demo stability: always include the tagline verbatim.
                if tagline_req:
                    text = _ensure_verbatim_line(text, required=tagline_req)
                
                normalized_whatsapp.append({
                    "id": i + 1,
                    "message_id": str(uuid.uuid4()),
                    "tone": msg.get("tone", f"Variant {i + 1}"),
                    "message": text,
                    "predicted_performance": msg.get("predicted_performance", "Good")
                })

            # Normalize Email variants
            email_variants_raw = result.get("email_variants", [])
            if not email_variants_raw and not result.get("whatsapp_variants"):
                 # Only fallback if AI didn't use new keys at all
                email_variants_raw = result.get("message_variants", [])

            if not email_variants_raw or len(email_variants_raw) < 3:
                default_tones = ["Professional", "Informative", "Direct"]
                while len(email_variants_raw) < 3:
                    idx = len(email_variants_raw)
                    biz_name = brand_context.get("business_name", "Our Team")
                    msg = f"Subject: Exciting news from {biz_name}!\n\nBody: Hi there, we are thrilled to announce our latest {campaign_idea[:40]} initiative.\n\nRegards, Team {biz_name}"
                    email_variants_raw.append({"id": idx + 1, "tone": default_tones[idx], "message": msg, "predicted_performance": "Good"})

            normalized_email = []
            for i, msg in enumerate(email_variants_raw[:3]):
                text = msg.get("message", "")
                biz_name = brand_context.get("business_name", "Our Team")
                # Aggressive replacement of common placeholders
                text = text.replace("[Team]", biz_name).replace("[Your Team]", biz_name)
                text = text.replace("[Brand Name]", biz_name).replace("{{brand_name}}", biz_name)
                text = text.replace("Our Brand", biz_name).replace("[Brand]", biz_name)

                if "subject:" not in text.lower():
                    text = f"Subject: Special Campaign Update\n\nBody: {text}\n\nRegards, Team {biz_name}"

                if tagline_req:
                    text = _ensure_verbatim_line(text, required=tagline_req)
                
                normalized_email.append({
                    "id": i + 1,
                    "message_id": str(uuid.uuid4()),
                    "tone": msg.get("tone", f"Variant {i + 1}"),
                    "message": text,
                    "predicted_performance": msg.get("predicted_performance", "Good")
                })

            # Legacy compatibility
            normalized_messages = normalized_whatsapp if content_type == "whatsapp" else normalized_email
            if content_type == "all":
                normalized_messages = normalized_whatsapp + normalized_email
            
            # Log messages to database (non-blocking)
            try:
                message_logs_data = []
                # Add WhatsApp logs
                if content_type in ["all", "whatsapp"]:
                    for m in normalized_whatsapp:
                        message_logs_data.append({
                            "caption_id": m["message_id"],
                            "user_id": user_id,
                            "campaign_id": campaign_id,
                            "campaign_idea": campaign_idea[:500] if campaign_idea else None,
                            "asset_type": AssetTypeEnum.WHATSAPP,
                            "caption_text": m["message"],
                            "hashtags": [],
                            "tone": m["tone"],
                            "generation_prompt": user_prompt[:1000] if user_prompt else None,
                            "model_used": self.model,
                            "variant_number": m["id"],
                            "predicted_performance": m.get("predicted_performance"),
                            "brand_tone_used": brand_context.get("tone_of_voice"),
                            "target_audience": target_audience,
                            "times_used": 0,
                            "tags": ["whatsapp"] + ([campaign_tone] if campaign_tone else []),
                            "is_favorite": False
                        })
                # Add Email logs
                if content_type in ["all", "emails"]:
                    for m in normalized_email:
                        message_logs_data.append({
                            "caption_id": m["message_id"],
                            "user_id": user_id,
                            "campaign_id": campaign_id,
                            "campaign_idea": campaign_idea[:500] if campaign_idea else None,
                            "asset_type": AssetTypeEnum.EMAIL,
                            "caption_text": m["message"],
                            "hashtags": [],
                            "tone": m["tone"],
                            "generation_prompt": user_prompt[:1000] if user_prompt else None,
                            "model_used": self.model,
                            "variant_number": m["id"],
                            "predicted_performance": m.get("predicted_performance"),
                            "brand_tone_used": brand_context.get("tone_of_voice"),
                            "target_audience": target_audience,
                            "times_used": 0,
                            "tags": ["emails"] + ([campaign_tone] if campaign_tone else []),
                            "is_favorite": False
                        })
                
                if message_logs_data:
                    await self.caption_repo.create_many(message_logs_data)
                    logger.info(f"✅ Logged {len(message_logs_data)} messages to database")
            except Exception as log_error:
                logger.error(f"⚠️ Failed to log messages: {log_error}")
            
            # Get image prompts (or provide placeholders)
            image_prompts = result.get("image_prompts")
            if not image_prompts:
                # Backward compatibility: accept old key if model returns it
                legacy = result.get("image_generation_prompts")
                if isinstance(legacy, list):
                    # Accept either [{"id":1,"prompt":"..."}, ...] or ["..."]
                    extracted: list[str] = []
                    for item in legacy:
                        if isinstance(item, str):
                            extracted.append(item)
                        elif isinstance(item, dict) and item.get("prompt"):
                            extracted.append(str(item["prompt"]))
                    image_prompts = extracted

            if not isinstance(image_prompts, list):
                image_prompts = []

            if not image_prompts:
                image_prompts = [
                    "Professional product photography with brand colors",
                    "Lifestyle shot showing product in use",
                    "Bold promotional graphic for social media",
                ]
            
            # Generate real images using Gemini (Only when explicitly requested via 'images' type)
            image_paths = []
            image_generation_prompt = ""
            asset_ids = []
            generate_images = content_type == "images"
            if generate_images:
                try:
                    image_service = get_image_generation_service()
                    image_result = await image_service.generate_campaign_images(
                        campaign_idea=campaign_idea,
                        brand_context=brand_context,
                        user_id=user_id,
                        aspect_ratio=aspect_ratio or "1:1",
                    )
                    
                    if image_result.get("success"):
                        image_paths = image_result.get("image_paths", [])
                        image_generation_prompt = image_result.get("image_prompt", "")
                        asset_ids = image_result.get("asset_ids", [])
                        logo_used = image_result.get("logo_used")
                        logo_warning = image_result.get("logo_warning")
                        logger.info("🖼️ Successfully generated %d images with %d assets saved", len(image_paths), len(asset_ids))
                    else:
                        logger.warning("⚠️ Image generation failed: %s", image_result.get("message"))
                except Exception as img_error:
                    logger.error("❌ Image generation error: %s", str(img_error))
                    # Continue without images - not critical to fail the entire request
            
            # Filter response based on content_type
            empty_captions = [{"id": 1, "caption_id": "", "tone": "N/A", "caption": "", "hashtags": [], "predicted_performance": "N/A"}]
            empty_messages = [{"id": 1, "message_id": "", "tone": "N/A", "message": "", "predicted_performance": "N/A"}]
            empty_hashtag_sets: list = []
            
            # Final output lists
            final_whatsapp = normalized_whatsapp
            final_email = normalized_email
            final_captions = normalized_captions
            final_hashtags = normalized_hashtag_sets

            # If generating only images, clear other fields in response
            if content_type == "images":
                final_captions = empty_captions
                final_messages = empty_messages
                final_hashtags = empty_hashtag_sets
                final_whatsapp = empty_messages
                final_email = empty_messages

            elif content_type == "captions":
                final_messages = empty_messages
                final_hashtags = empty_hashtag_sets
                final_whatsapp = empty_messages
                final_email = empty_messages
            elif content_type == "hashtags":
                final_captions = empty_captions
                final_messages = empty_messages
                final_whatsapp = empty_messages
                final_email = empty_messages
            elif content_type == "whatsapp":
                final_captions = empty_captions
                final_hashtags = empty_hashtag_sets
                final_email = empty_messages
            elif content_type == "emails":
                final_captions = empty_captions
                final_hashtags = empty_hashtag_sets
                final_whatsapp = empty_messages
            
            # Final brand-lock validation warnings (for UI visibility).
            # Note: we already retried earlier pre-normalization; this is for transparency.
            validation_warnings = _validate_brand_lock(
                captions=normalized_captions,
                whatsapp=normalized_whatsapp,
                emails=normalized_email,
                ct=content_type,
            )

            logger.info("✅ Content generation completed successfully")
            return {
                "success": True,
                "platform_type": platform_type,
                "caption_variants": final_captions,
                "best_caption_id": ml_best_id if 'ml_best_id' in dir() else result.get("best_caption_id", 1),
                "hashtag_sets": final_hashtags[:3],
                "best_hashtag_set_id": best_hashtag_set_id,
                "whatsapp_variants": final_whatsapp,
                "email_variants": final_email,
                "message_variants": normalized_messages, # Legacy support
                "best_message_id": result.get("best_message_id", 1),
                "image_prompts": image_prompts[:3],
                "image_paths": image_paths,
                "asset_ids": asset_ids,
                "image_generation_prompt": image_generation_prompt,
                "reasoning": result.get("reasoning", ""),
                "validation_warnings": validation_warnings,
                "logo_used": logo_used,
                "logo_warning": logo_warning,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON Parse Error: {e}")
            logger.error(f"Failed content: {content[:500] if 'content' in locals() else 'N/A'}")
            return {
                "success": False,
                "error": "Unable to process AI response",
                "detail": "The content generation service encountered a formatting error. Please try again."
            }
        except Exception as e:
            logger.error(f"❌ Content generation failed: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": "Content generation unavailable",
                "detail": "We're experiencing technical difficulties. Please try again shortly."
            }


# Singleton instance
_content_service: Optional[ContentGenerationService] = None


def get_content_generation_service() -> ContentGenerationService:
    """Get or create the content generation service instance."""
    global _content_service
    if _content_service is None:
        _content_service = ContentGenerationService()
    return _content_service
