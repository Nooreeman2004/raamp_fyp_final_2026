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
        """Build the brand context section of the prompt."""
        sections = []
        
        if brand_context.get("business_name"):
            sections.append(f"Business Name: {brand_context['business_name']}")
        
        if brand_context.get("tagline"):
            sections.append(f"Brand Tagline: {brand_context['tagline']}")
        
        if brand_context.get("tone_of_voice"):
            sections.append(f"Default Brand Tone: {brand_context['tone_of_voice']}")
        
        if brand_context.get("restaurant_theme"):
            sections.append(f"Brand Theme/Ambiance: {brand_context['restaurant_theme']}")
        
        if brand_context.get("business_type"):
            sections.append(f"Business Type: {brand_context['business_type']}")
        
        if brand_context.get("primary_color") or brand_context.get("secondary_color"):
            colors = []
            if brand_context.get("primary_color"):
                colors.append(f"Primary: {brand_context['primary_color']}")
            if brand_context.get("secondary_color"):
                colors.append(f"Secondary: {brand_context['secondary_color']}")
            sections.append(f"Brand Colors: {', '.join(colors)}")
        
        if brand_context.get("brand_logo_url"):
            sections.append(f"Brand Logo: {brand_context['brand_logo_url']} (incorporate visual brand identity into image prompts)")
            
        if brand_context.get("specialties"):
            sections.append(f"Expert Specialties: {', '.join(brand_context['specialties'])}")
        
        if not sections:
            return "Brand Context: No brand information available. Generate generic but professional content."
        
        return "BRAND VOICE GUIDELINES:\n" + "\n".join(f"• {s}" for s in sections)
    
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
        
        # Build the prompt
        prompt_parts = [
            brand_section,
            ""
        ]
        
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
            "3. Three WhatsApp Messages: Catchy, SHORT, casual, direct. NO subject lines. Start with 'Hey {name}!'",
            f"4. Three Email Campaigns: LONG, professional. Format EXACTLY as:\n   Subject: [Subject Line]\n   Body: [Email Body]\n   Regards,\n   Team {brand_context.get('business_name', 'Our Brand')}",
            "5. Three detailed image generation prompts.",
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
            '  "message_variants": [',
            '    { "id": 1, "tone": "Friendly", "message": "your whatsapp/email content here", "predicted_performance": "High" },',
            "    ...",
            "  ],",
            '  "image_generation_prompts": [',
            '    { "id": 1, "prompt": "detailed image prompt here" },',
            "    ...",
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
        content_type: str = "all"
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
            
            # Select appropriate system prompt based on platform type
            system_prompt = self._get_system_prompt(platform_type)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            logger.info(f"📤 Calling GenAI SDK — model: {self.model}, platform: {platform_type}, content_type: {content_type}")
            logger.info(f"📝 Prompt length: {len(full_prompt)} chars")
            
            # Call Google GenAI SDK directly (bypasses OpenAI-compat which has model coverage gaps)
            try:
                response = await asyncio.to_thread(
                    lambda: self.client.models.generate_content(
                        model=self.model,
                        contents=full_prompt,
                        config=genai_types.GenerateContentConfig(
                            temperature=0.8,
                            max_output_tokens=4096,
                            response_mime_type="application/json",
                        )
                    )
                )
                raw_text = response.text
                logger.info(f"✅ GenAI SDK responded — {len(raw_text)} chars")
            except Exception as api_error:
                logger.error(f"❌ GenAI SDK call failed: {type(api_error).__name__}: {api_error}")
                logger.error(f"   Model: {self.model}")
                import traceback
                logger.error(f"   Traceback: {traceback.format_exc()}")
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

            # Extract JSON from the response (strip any markdown fences)
            content = raw_text.strip()
            logger.info(f"📥 Raw response preview: {content[:300]}...")
            
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
                logger.info("✅ Successfully parsed JSON response")
            except json.JSONDecodeError:
                logger.warning("⚠️ Direct JSON parse failed, trying regex extraction...")
                match = re.search(r'\{[\s\S]*\}', content)
                if match:
                    try:
                        result = json.loads(match.group(0))
                        logger.info("✅ Successfully parsed JSON via regex extraction")
                    except json.JSONDecodeError as json_error:
                        logger.error(f"❌ Failed to parse JSON after regex: {json_error}")
                        logger.error(f"Response text: {content[:1000]}")
                        raise
                else:
                    logger.error(f"❌ No JSON block found in response. Raw: {content[:500]}")
                    raise json.JSONDecodeError("No JSON block found", content, 0)
            
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

                normalized_captions.append({
                    "id": variant.get("id", i + 1),
                    "caption_id": caption_id,  # Add caption_id to variant
                    "tone": variant.get("tone", f"Variant {i + 1}"),
                    "caption": variant.get("caption", ""),
                    "hashtags": hashtags,
                    "predicted_performance": variant.get("predicted_performance", "Good")
                })
            
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
            
            # Normalize message variants
            message_variants = result.get("message_variants", [])
            if not message_variants or len(message_variants) < 3:
                # Create default messages
                default_tones = ["Professional", "Friendly", "Urgent"]
                while len(message_variants) < 3:
                    idx = len(message_variants)
                    biz_name = brand_context.get("business_name", "Our Team")
                    if content_type == "whatsapp" or "whatsapp" in campaign_idea.lower():
                        msg = f"Hey {{name}}! We noticed you love our {biz_name} products. We've got a special {campaign_idea[:30]} campaign running just for you! Check it out here: [Link]"
                    else:
                        msg = f"Subject: Exciting news from {biz_name}!\n\nBody: Hi there, we are thrilled to announce our latest {campaign_idea[:40]} initiative.\n\nRegards, Team {biz_name}"
                    
                    message_variants.append({
                        "id": idx + 1,
                        "tone": default_tones[idx],
                        "message": msg,
                        "predicted_performance": "Good"
                    })
            
            # Generate message_ids and normalize
            message_ids = [str(uuid.uuid4()) for _ in range(min(3, len(message_variants)))]
            normalized_messages = []
            for i, msg in enumerate(message_variants[:3]):
                message_id = message_ids[i] if i < len(message_ids) else str(uuid.uuid4())
                text = msg.get("message", "")
                
                # Post-processing: Enforce Formatting
                biz_name = brand_context.get("business_name", "Our Team")
                if (content_type == "whatsapp" or "whatsapp" in campaign_idea.lower()) and "hey {name}" not in text.lower():
                    if not text.startswith("Hey"):
                        text = f"Hey {{name}}! " + text
                elif (content_type == "emails" or "email" in campaign_idea.lower()) and "subject:" not in text.lower():
                    text = f"Subject: Special Campaign Update\n\nBody: {text}\n\nRegards, Team {biz_name}"

                normalized_messages.append({
                    "id": msg.get("id", i + 1),
                    "message_id": message_id,  # Add message_id for tracking
                    "tone": msg.get("tone", f"Variant {i + 1}"),
                    "message": text,
                    "predicted_performance": msg.get("predicted_performance", "Good")
                })
            
            # Log messages to database (non-blocking)
            try:
                # Determine asset type based on content_type
                message_asset_type = AssetTypeEnum.WHATSAPP if content_type == "whatsapp" else AssetTypeEnum.EMAIL
                
                message_logs_data = []
                for message_data in normalized_messages:
                    message_log = {
                        "caption_id": message_data["message_id"],  # Using caption_id field for message_id
                        "user_id": user_id,
                        "campaign_id": campaign_id,
                        "campaign_idea": campaign_idea[:500] if campaign_idea else None,
                        "asset_type": message_asset_type,
                        "caption_text": message_data["message"],
                        "hashtags": [],  # Messages don't have hashtags
                        "tone": message_data["tone"],
                        "generation_prompt": user_prompt[:1000] if user_prompt else None,
                        "model_used": self.model,
                        "variant_number": message_data["id"],
                        "predicted_performance": message_data.get("predicted_performance"),
                        "brand_tone_used": brand_context.get("tone_of_voice"),
                        "target_audience": target_audience,
                        "times_used": 0,
                        "tags": [content_type] + ([campaign_tone] if campaign_tone else []),
                        "is_favorite": False
                    }
                    message_logs_data.append(message_log)
                
                await self.caption_repo.create_many(message_logs_data)
                logger.info(f"✅ Logged {len(message_logs_data)} {content_type} messages to database")
            except Exception as log_error:
                logger.error(f"⚠️ Failed to log messages: {log_error}")
            
            # Get image prompts (or provide placeholders)
            image_prompts = result.get("image_prompts", [
                "Professional product photography with brand colors",
                "Lifestyle shot showing product in use",
                "Bold promotional graphic for social media"
            ])
            
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
                        user_id=user_id
                    )
                    
                    if image_result.get("success"):
                        image_paths = image_result.get("image_paths", [])
                        image_generation_prompt = image_result.get("image_prompt", "")
                        asset_ids = image_result.get("asset_ids", [])
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
            
            # If generating only images, clear other fields in response
            if content_type == "images":
                normalized_captions = empty_captions
                normalized_messages = empty_messages
                normalized_hashtag_sets = empty_hashtag_sets
                # No text logging needed for image-only generation? 
                # Actually text generation still happened, we just filter it out here.

            elif content_type == "captions":
                # Only captions + their hashtags
                normalized_messages = empty_messages
                normalized_hashtag_sets = empty_hashtag_sets
            elif content_type == "hashtags":
                # Only hashtag sets
                normalized_captions = empty_captions
                normalized_messages = empty_messages
            elif content_type in ("whatsapp", "emails"):
                # Only messages (+ images for whatsapp? Wait user doesn't want images in campaign path)
                normalized_captions = empty_captions
                normalized_hashtag_sets = empty_hashtag_sets
            # content_type == "all" → return everything (no filtering) but images will be [] because generate_images is False
            
            logger.info("✅ Content generation completed successfully")
            return {
                "success": True,
                "platform_type": platform_type,
                "caption_variants": normalized_captions,
                "best_caption_id": result.get("best_caption_id", 1),
                "hashtag_sets": normalized_hashtag_sets[:3],
                "message_variants": normalized_messages,
                "best_message_id": result.get("best_message_id", 1),
                "image_prompts": image_prompts[:3],
                "image_paths": image_paths,
                "asset_ids": asset_ids,
                "image_generation_prompt": image_generation_prompt,
                "reasoning": result.get("reasoning", ""),
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
