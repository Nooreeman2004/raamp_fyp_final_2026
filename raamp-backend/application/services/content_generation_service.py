"""
Content Generation Service
==========================
AI-powered service for generating ALL social media content types in one call.
Generates: Captions, Hashtags, WhatsApp/Email messages, and Image prompts.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from openai import AsyncOpenAI
from dotenv import load_dotenv

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
    """
    
    # System prompt for unified content generation
    SYSTEM_PROMPT = """You are an elite social media creative director with expertise in viral content creation and marketing campaigns. Your task is to generate a COMPLETE marketing package in a single response.

## WHAT YOU GENERATE:
1. **Social Media Captions + Hashtags** (3 variants) - For Instagram, Facebook posts
2. **Standalone Hashtag Sets** (3 sets) - Optimized for maximum reach
3. **WhatsApp/Email Campaign Messages** (3 variants) - Professional direct outreach
4. **Image Prompts** (3 prompts) - Descriptions for AI image generation

## WORKFLOW:

### STEP 1: UNDERSTAND
Analyze the campaign:
- Core message and value proposition
- Target audience psychology
- Brand voice and tone requirements

### STEP 2: GENERATE CAPTIONS (3 variants)
Create three DISTINCTLY different social media posts:
- Variant 1: "Vibrant & Direct" - Bold, action-oriented, emojis, urgency
- Variant 2: "Informative & Engaging" - Educational, trust-building, benefits
- Variant 3: "Curious & Playful" - Questions, humor, interaction hooks

### STEP 3: GENERATE HASHTAG SETS (3 sets)
Create three different hashtag strategies:
- Set 1: "Broad Reach" - Popular, trending hashtags (8-10)
- Set 2: "Niche Specific" - Industry/topic specific (8-10)
- Set 3: "Mixed Strategy" - Combination of broad + niche (8-10)

### STEP 4: GENERATE MESSAGES (3 variants)
Create three WhatsApp/Email messages:
- Variant 1: "Professional" - Formal business tone
- Variant 2: "Friendly" - Warm, personal connection
- Variant 3: "Urgent" - Time-sensitive, FOMO-driven

### STEP 5: GENERATE IMAGE PROMPTS (3 prompts)
Create three image generation prompts:
- Describe visual style, colors, mood, composition
- Include brand elements mentioned
- Suitable for social media aspect ratios

## CRITICAL RULES:
1. Output ONLY valid JSON - no text outside JSON
2. Each caption must be platform-appropriate (150-200 chars)
3. Hashtags must start with # and be relevant
4. Messages must be concise but complete (greeting + value + CTA)
5. Image prompts must be detailed and visual

## OUTPUT FORMAT (strict JSON):
{
    "caption_variants": [
        {
            "id": 1,
            "tone": "Vibrant & Direct",
            "caption": "Hook them here 🔥 Then deliver the message!",
            "hashtags": ["#Specific1", "#Trending2", "#Niche3", "#Brand4"],
            "predicted_performance": "Best"
        },
        {
            "id": 2,
            "tone": "Informative & Engaging",
            "caption": "Did you know...? Share valuable insight here.",
            "hashtags": ["#Educational1", "#Industry2", "#Trust3", "#Value4"],
            "predicted_performance": "Good"
        },
        {
            "id": 3,
            "tone": "Curious & Playful",
            "caption": "What if...? 🤔 Engage with a question!",
            "hashtags": ["#Fun1", "#Community2", "#Engage3", "#Trend4"],
            "predicted_performance": "Experimental"
        }
    ],
    "best_caption_id": 1,
    "hashtag_sets": [
        ["#Popular1", "#Trending2", "#Viral3", "#Reach4", "#Growth5", "#Social6", "#Marketing7", "#Brand8"],
        ["#Niche1", "#Industry2", "#Specific3", "#Expert4", "#Professional5", "#Specialized6", "#Topic7", "#Focus8"],
        ["#Mixed1", "#Balanced2", "#Strategic3", "#Targeted4", "#Optimized5", "#Smart6", "#Growth7", "#Niche8"]
    ],
    "best_hashtag_set_id": 1,
    "message_variants": [
        {
            "id": 1,
            "tone": "Professional",
            "message": "Dear [Name],\\n\\nWe're excited to share...\\n\\nBest regards,\\n[Brand]",
            "predicted_performance": "Best"
        },
        {
            "id": 2,
            "tone": "Friendly",
            "message": "Hey there! 👋\\n\\nWe've got something special...\\n\\nCheers!",
            "predicted_performance": "Good"
        },
        {
            "id": 3,
            "tone": "Urgent",
            "message": "⏰ Limited time!\\n\\nDon't miss out on...\\n\\nAct now!",
            "predicted_performance": "Good"
        }
    ],
    "best_message_id": 1,
    "image_prompts": [
        "Professional product photography of [item], modern minimalist style, soft natural lighting, brand colors, clean white background, 4:5 aspect ratio for Instagram",
        "Lifestyle shot showing [product/service] in use, warm tones, happy customers, authentic feel, urban setting, 1:1 square format",
        "Bold promotional graphic with [offer], vibrant brand colors, modern typography, eye-catching design, suitable for stories 9:16"
    ],
    "reasoning": "Strategy explanation: why these approaches will work for this campaign"
}"""

    def __init__(self):
        """Initialize the content generation service."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = os.getenv("OPENAI_GENERATION_MODEL", "gpt-4o-mini")
        
        logger.info(f"ContentGenerationService initialized with model: {self.model}")
    
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
        
        if not sections:
            return "Brand Context: No brand information available. Generate generic but professional content."
        
        return "BRAND VOICE GUIDELINES:\n" + "\n".join(f"• {s}" for s in sections)
    
    def _build_user_prompt(
        self,
        campaign_idea: str,
        target_audience: Optional[str],
        campaign_tone: Optional[str],
        brand_context: Dict[str, Any]
    ) -> str:
        """Build the complete user prompt for unified content generation."""
        
        # Brand context section
        brand_section = self._build_brand_context_prompt(brand_context)
        
        # Build the prompt
        prompt_parts = [
            brand_section,
            "",
            "CAMPAIGN DETAILS:",
            f"Campaign Idea: {campaign_idea}"
        ]
        
        if target_audience:
            prompt_parts.append(f"Target Audience: {target_audience}")
        
        if campaign_tone:
            prompt_parts.append(f"Campaign Tone Override: {campaign_tone} (prioritize this tone while keeping brand voice)")
        elif brand_context.get("tone_of_voice"):
            prompt_parts.append(f"Using Default Brand Tone: {brand_context['tone_of_voice']}")
        
        prompt_parts.extend([
            "",
            "TASK: Generate a COMPLETE marketing package following the exact JSON format.",
            "Include ALL of the following:",
            "1. Three caption variants with hashtags (for social media posts)",
            "2. Three standalone hashtag sets (broad reach, niche, mixed)",
            "3. Three WhatsApp/Email message variants (professional, friendly, urgent)",
            "4. Three image generation prompts (product shot, lifestyle, promo graphic)",
            "",
            "Remember: Output ONLY valid JSON, no text before or after."
        ])
        
        return "\n".join(prompt_parts)
    
    async def generate_content(
        self,
        campaign_idea: str,
        brand_context: Dict[str, Any],
        target_audience: Optional[str] = None,
        campaign_tone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate ALL content types in a single AI call.
        
        Args:
            campaign_idea: The campaign vision/idea from user
            brand_context: Brand information from database
            target_audience: Optional target audience description
            campaign_tone: Optional tone override for this campaign
            
        Returns:
            Dictionary with all content types and metadata
        """
        try:
            # Build the user prompt
            user_prompt = self._build_user_prompt(
                campaign_idea=campaign_idea,
                target_audience=target_audience,
                campaign_tone=campaign_tone,
                brand_context=brand_context
            )
            
            logger.info("Generating unified content package")
            logger.debug(f"User prompt: {user_prompt[:500]}...")
            
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.8,  # Higher temperature for creative variety
                max_tokens=2500,  # Increased for more content
                response_format={"type": "json_object"}  # Ensure JSON response
            )
            
            # Parse the response
            content = response.choices[0].message.content
            logger.debug(f"Raw AI response: {content}")
            
            # Parse JSON
            result = json.loads(content)
            
            # Validate and normalize caption variants
            caption_variants = result.get("caption_variants", [])
            if not caption_variants or len(caption_variants) < 3:
                # Fallback if not enough variants
                while len(caption_variants) < 3:
                    caption_variants.append({
                        "id": len(caption_variants) + 1,
                        "tone": f"Variant {len(caption_variants) + 1}",
                        "caption": "Content generation in progress...",
                        "hashtags": ["#Brand", "#Marketing"],
                        "predicted_performance": "Good"
                    })
            
            normalized_captions = []
            for i, variant in enumerate(caption_variants[:3]):
                normalized_captions.append({
                    "id": variant.get("id", i + 1),
                    "tone": variant.get("tone", f"Variant {i + 1}"),
                    "caption": variant.get("caption", ""),
                    "hashtags": variant.get("hashtags", []),
                    "predicted_performance": variant.get("predicted_performance", "Good")
                })
            
            # Normalize hashtag sets
            hashtag_sets = result.get("hashtag_sets", [])
            if not hashtag_sets or len(hashtag_sets) < 3:
                # Generate from caption hashtags as fallback
                hashtag_sets = [
                    normalized_captions[0].get("hashtags", [])[:8],
                    normalized_captions[1].get("hashtags", [])[:8] if len(normalized_captions) > 1 else [],
                    normalized_captions[2].get("hashtags", [])[:8] if len(normalized_captions) > 2 else []
                ]
            
            # Normalize message variants
            message_variants = result.get("message_variants", [])
            if not message_variants or len(message_variants) < 3:
                # Create default messages
                default_tones = ["Professional", "Friendly", "Urgent"]
                while len(message_variants) < 3:
                    idx = len(message_variants)
                    message_variants.append({
                        "id": idx + 1,
                        "tone": default_tones[idx],
                        "message": f"Message variant {idx + 1} - customize based on campaign",
                        "predicted_performance": "Good"
                    })
            
            normalized_messages = []
            for i, msg in enumerate(message_variants[:3]):
                normalized_messages.append({
                    "id": msg.get("id", i + 1),
                    "tone": msg.get("tone", f"Variant {i + 1}"),
                    "message": msg.get("message", ""),
                    "predicted_performance": msg.get("predicted_performance", "Good")
                })
            
            # Get image prompts (or provide placeholders)
            image_prompts = result.get("image_prompts", [
                "Professional product photography with brand colors",
                "Lifestyle shot showing product in use",
                "Bold promotional graphic for social media"
            ])
            
            return {
                "success": True,
                "caption_variants": normalized_captions,
                "best_caption_id": result.get("best_caption_id", 1),
                "hashtag_sets": hashtag_sets[:3],
                "message_variants": normalized_messages,
                "best_message_id": result.get("best_message_id", 1),
                "image_prompts": image_prompts[:3],
                "reasoning": result.get("reasoning", ""),
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            return {
                "success": False,
                "error": "Failed to parse AI response",
                "detail": str(e)
            }
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            return {
                "success": False,
                "error": "Content generation failed",
                "detail": str(e)
            }


# Singleton instance
_content_service: Optional[ContentGenerationService] = None


def get_content_generation_service() -> ContentGenerationService:
    """Get or create the content generation service instance."""
    global _content_service
    if _content_service is None:
        _content_service = ContentGenerationService()
    return _content_service
