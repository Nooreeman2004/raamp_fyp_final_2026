"""
Image Generation Service
========================
AI-powered service for generating brand-aligned social media images using Google Gemini.
Generates image prompts and creates visual variations based on campaign ideas and brand context.
"""

import os
import asyncio
import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from google.genai import types as genai_types
from dotenv import load_dotenv
import httpx  # for fetching brand logos

from infrastructure.repositories.asset_repository import AssetRepository
from infrastructure.database.models.asset_model import AssetType, GenerationSource
from application.services.cloudinary_service import CloudinaryService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ImageGenerationService:
    """
    Service for generating AI-powered social media images.
    
    Uses Google Gemini to:
    1. Generate detailed image prompts from campaign ideas + brand context
    2. Generate 3 image variations using Gemini image generation
    """
    
    # System prompt for generating image prompts from user input
    PROMPT_GENERATOR_SYSTEM_PROMPT = """You are an expert creative director, brand strategist, and AI image prompt engineer.

Your task is to generate a highly detailed, professional image generation prompt for social media marketing.

## CRITICAL RULES:

1. **Campaign Vision Priority**:
   - The user's specific campaign idea or theme (e.g., 'University Admissions', 'Holiday Special') MUST be the absolute primary focus of the visual.
   - If the user provides specific details like 'Audience', 'Highlights', 'Programs', or 'Important Dates', incorporate EVERY SINGLE ONE of these into the visual composition.
   - Do NOT ignore specific industry details in the request in favor of general brand context.
   - Integrate the brand identity (name, logo cues, colors) INTO the requested scene naturally.

2. **Brand Consistency**:
   - Use the brand's color palette where possible.
   - Match the overall brand tone (e.g., playful, luxury) while respecting the campaign's specific mood.

3. **Social Media Optimization**:
   - Design for Instagram/Facebook feed posts (1:1 or 4:5 aspect ratio).
   - Ensure visuals are scroll-stopping and professional.

## OUTPUT FORMAT:

Generate a single, comprehensive image generation prompt (150-300 words).
IMPORTANT: PRIORITY ORDER: Focus exactly on the campaign's visual theme. Never ask for clarification."""

    def __init__(self):
        """Initialize the image generation service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
        self.image_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
        self.output_folder = Path("generated_images")
        self.output_folder.mkdir(exist_ok=True)
        self.asset_repo = AssetRepository()
        self.cloudinary_service = CloudinaryService()
        
        logger.info(f"ImageGenerationService initialized - Text: {self.text_model}, Image: {self.image_model}")
    
    def _build_brand_context_section(self, brand_context: Dict[str, Any]) -> str:
        """Build the brand context section for the prompt generator."""
        sections = []
        
        if brand_context.get("business_name"):
            sections.append(f"Brand Name: {brand_context['business_name']}")
        
        if brand_context.get("business_type"):
            sections.append(f"Industry: {brand_context['business_type']}")
        
        if brand_context.get("tone_of_voice"):
            sections.append(f"Brand Tone: {brand_context['tone_of_voice']}")
        
        if brand_context.get("restaurant_theme"):
            sections.append(f"Brand Style/Theme: {brand_context['restaurant_theme']}")
        
        if brand_context.get("primary_color"):
            sections.append(f"Primary Brand Color: {brand_context['primary_color']}")
        
        if brand_context.get("secondary_color"):
            sections.append(f"Secondary Brand Color: {brand_context['secondary_color']}")
        
        if brand_context.get("tagline"):
            sections.append(f"Brand Tagline: {brand_context['tagline']}")
        
        if brand_context.get("brand_logo_url"):
            sections.append(f"Brand Logo: {brand_context['brand_logo_url']} (incorporate visual brand identity cues)")
            
        if brand_context.get("specialties"):
            sections.append(f"Specialties: {', '.join(brand_context['specialties'])}")
        
        if not sections:
            return "Brand Context: Limited brand information available. Generate generic but professional content suitable for social media."
        
        return "## BRAND ASSETS PROVIDED:\n" + "\n".join(f"- {s}" for s in sections)
    
    def generate_image_prompt(
        self, 
        campaign_idea: str, 
        brand_context: Dict[str, Any]
    ) -> str:
        """
        Generate a detailed image prompt using Gemini.
        
        Args:
            campaign_idea: User's campaign description
            brand_context: Brand information from database
            
        Returns:
            Detailed image generation prompt
        """
        try:
            brand_section = self._build_brand_context_section(brand_context)
            logo_url = brand_context.get("brand_logo_url") or brand_context.get("logo_url")
            
            user_message = f"""{brand_section}

## USER CAMPAIGN REQUEST:
{campaign_idea}

## TASK:
Generate a detailed, specific image generation prompt for social media marketing.
If any brand information is missing, make reasonable creative assumptions based on the campaign idea.
Do NOT ask for clarification — just generate the best possible prompt you can."""

            logger.info("Generating image prompt with Gemini (logo_url=%s)", logo_url or "none")

            # Build multimodal contents: include logo image if available
            contents: list = []
            if logo_url:
                try:
                    with httpx.Client(timeout=8.0) as http:
                        logo_resp = http.get(logo_url)
                    if logo_resp.status_code == 200:
                        img_bytes = logo_resp.content
                        mime = logo_resp.headers.get("content-type", "image/png").split(";")[0]
                        contents.append(
                            types.Part(
                                inline_data=types.Blob(mime_type=mime, data=img_bytes)
                            )
                        )
                        contents.append(
                            types.Part(
                                text=(
                                    "The image above is the brand's LOGO. "
                                    "Carefully analyse its visual style, color palette, typography, and aesthetic. "
                                    "Incorporate these cues directly into the image prompt you generate so the output "
                                    "aligns perfectly with the brand's identity.\n\n" + user_message
                                )
                            )
                        )
                        logger.info("✅ Logo fetched (%d bytes, %s) — passing to Gemini", len(img_bytes), mime)
                    else:
                        logger.warning("⚠️ Logo fetch failed (%d) — proceeding text-only", logo_resp.status_code)
                        contents = [self.PROMPT_GENERATOR_SYSTEM_PROMPT + "\n\n" + user_message]
                except Exception as logo_err:
                    logger.warning("⚠️ Could not fetch logo: %s — proceeding text-only", logo_err)
                    contents = [self.PROMPT_GENERATOR_SYSTEM_PROMPT + "\n\n" + user_message]
            else:
                contents = [self.PROMPT_GENERATOR_SYSTEM_PROMPT + "\n\n" + user_message]
            
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=contents if logo_url and len(contents) > 1
                    else f"{self.PROMPT_GENERATOR_SYSTEM_PROMPT}\n\n{user_message}",
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=800
                )
            )
            
            image_prompt = response.text.strip()
            
            # If AI still refuses (shouldn't happen anymore), use campaign idea directly
            if "CLARIFICATION NEEDED" in image_prompt:
                logger.warning("⚠️ AI asked for clarification despite instructions — using campaign idea as direct prompt")
                return (
                    f"Professional social media marketing image for: {campaign_idea}. "
                    "Modern design, high-quality photography, vibrant colors, "
                    "clean composition, suitable for Instagram feed posts (1:1 ratio), "
                    "eye-catching and scroll-stopping."
                )
            
            logger.info("Image prompt generated successfully")
            return image_prompt
            
        except Exception as e:
            logger.error("Image prompt generation failed: %s", str(e))
            # Return a fallback prompt instead of raising so generation can still proceed
            return (
                f"Professional social media marketing image for: {campaign_idea}. "
                "High-quality photography, vibrant colors, clean composition for Instagram."
            )
    
    async def _generate_single_image(
        self, 
        image_prompt: str, 
        filename: str,
        aspect_ratio: str = "1:1"
    ) -> Optional[str]:
        """
        Generate a single image using a multi-strategy approach with retry.
        
        Returns: File path if successful, None otherwise
        """
        # Try up to 2 times for each image variation
        for attempt in range(1, 3):
            logger.info("🎨 Generating image attempt %d/2 for: %s", attempt, filename)
            
            # --- Strategy 1: Gemini generate_content with IMAGE modality ---
            try:
                response = self.client.models.generate_content(
                    model=self.image_model,
                    contents=image_prompt,
                    config=genai_types.GenerateContentConfig(
                        response_modalities=["TEXT", "IMAGE"]
                    )
                )
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data is not None:
                            img_bytes = part.inline_data.data
                            with open(filename, "wb") as f:
                                f.write(img_bytes)
                            logger.info("✅ [Strategy 1] Image saved: %s (attempt %d)", filename, attempt)
                            return filename
                logger.warning("⚠️ [Strategy 1] No inline_data in response (attempt %d)", attempt)
            except Exception as e:
                logger.warning("⚠️ [Strategy 1] failed: %s (attempt %d)", str(e), attempt)

            # --- Strategy 2: Imagen API generate_image ---
            try:
                response = self.client.models.generate_image(
                    model=self.image_model,
                    prompt=image_prompt,
                    config=types.GenerateImageConfig(
                        number_of_images=1,
                        aspect_ratio=aspect_ratio
                    )
                )
                if response.generated_images and len(response.generated_images) > 0:
                    image_obj = response.generated_images[0]
                    saved = self._save_image_object(image_obj, filename)
                    if saved:
                        logger.info("✅ [Strategy 2] Image saved (attempt %d)", attempt)
                        return filename
            except Exception as e:
                logger.warning("⚠️ [Strategy 2] failed: %s (attempt %d)", str(e), attempt)
            
            if attempt < 2:
                # Add a small delay between retries
                await asyncio.sleep(1)

        logger.error("❌ All image generation strategies failed for: %s after 2 attempts", filename)
        return None

    def _save_image_object(self, image_obj, filename: str) -> bool:
        """Helper to save an image object returned by Imagen API."""
        try:
            # Strategy A: PIL Image save method via .image
            if hasattr(image_obj, 'image') and hasattr(image_obj.image, 'save'):
                image_obj.image.save(filename)
                return True
            # Strategy B: Direct save method
            if hasattr(image_obj, 'save'):
                image_obj.save(filename)
                return True
            # Strategy C: Raw bytes via image_bytes attribute
            if hasattr(image_obj, 'image_bytes') and image_obj.image_bytes:
                with open(filename, 'wb') as f:
                    f.write(image_obj.image_bytes)
                return True
            # Strategy D: Raw bytes via .image.data (some SDK versions)
            if hasattr(image_obj, 'image') and hasattr(image_obj.image, 'image_bytes'):
                with open(filename, 'wb') as f:
                    f.write(image_obj.image.image_bytes)
                return True
            logger.warning("⚠️ Unknown image object type: %s", type(image_obj))
            return False
        except Exception as e:
            logger.error("❌ Failed to save image object: %s", str(e))
            return False
    
    async def generate_images(
        self, 
        image_prompt: str, 
        campaign_id: Optional[str] = None,
        count: int = 3
    ) -> List[str]:
        """
        Generate multiple image variations in parallel.
        
        Args:
            image_prompt: Detailed prompt for image generation
            campaign_id: Optional ID to namespace the images
            count: Number of variations to generate (default 3)
            
        Returns:
            List of URLs for successfully generated images
        """
        if campaign_id:
            output_dir = self.output_folder / campaign_id
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_folder / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("Generating %d image variations to %s", count, output_dir)
        
        # Generate images in parallel
        tasks = []
        for i in range(count):
            filename = str(output_dir / f"variation_{i+1}.png")
            tasks.append(self._generate_single_image(image_prompt, filename))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None values and exceptions, and log errors
        successful_images = []
        for i, r in enumerate(results):
            if r is not None and not isinstance(r, Exception):
                successful_images.append(r)
            else:
                logger.error("❌ Image variation %d failed: %s", i+1, r)
        
        logger.info("Successfully generated %d/%d images", len(successful_images), count)
        
        # Ensure we always return at least one image if any succeeded
        if not successful_images:
             logger.error("❌ NO IMAGES GENERATED AT ALL")
        
        # Convert file paths to URLs
        image_urls = []
        for file_path in successful_images:
            # Convert absolute path to relative URL
            # Example: generated_images/20240305_143022/variation_1.png -> /api/generated/20240305_143022/variation_1.png
            relative_path = Path(file_path).relative_to(self.output_folder)
            url = f"/api/generated/{relative_path}".replace("\\", "/")
            image_urls.append(url)
        
        return image_urls
    
    async def generate_campaign_images(
        self, 
        campaign_idea: str, 
        brand_context: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Complete pipeline: Generate image prompt + generate images + save as assets.
        
        Args:
            campaign_idea: User's campaign description
            brand_context: Brand information from database
            user_id: User identifier for asset ownership
            
        Returns:
            Dictionary with image prompt, image paths, and asset IDs
        """
        try:
            logger.info("🎨 Starting 3-image generation for campaign: %s", campaign_idea[:50])
            
            # Step 1: Generate the image prompt (always proceeds — no 'clarification needed' early exit)
            logger.info("📝 Step 1: Generating image prompt using %s", self.text_model)
            image_prompt = self.generate_image_prompt(campaign_idea, brand_context)
            logger.info("✅ Image prompt generated: %s...", image_prompt[:100])
            
            # Step 2: Generate 3 images
            logger.info("🖼️ Step 2: Generating 3 images using %s", self.image_model)
            campaign_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_paths = await self.generate_images(image_prompt, campaign_id, count=3)
            
            if not image_paths:
                logger.error("❌ No images were generated")
                return {
                    "success": False,
                    "error": "Image generation failed",
                    "message": "No images were generated. Please try again."
                }
            
            logger.info("✅ Successfully generated %d images", len(image_paths))
            
            # Step 3: Save each generated image as an asset in the database
            logger.info("💾 Step 3: Saving %d images as reusable assets", len(image_paths))
            asset_ids = []
            for idx, image_url in enumerate(image_paths, start=1):
                try:
                    # Convert URL back to file path to get file size
                    # URL format: /api/generated/20240305_143022/variation_1.png
                    relative_path = image_url.replace("/api/generated/", "")
                    file_path = self.output_folder / relative_path
                    
                    file_size = 0
                    if file_path.exists():
                        file_size = file_path.stat().st_size
                    
                    # Upload to Cloudinary (optional but recommended for public access)
                    cloudinary_url = None
                    if self.cloudinary_service.is_available:
                        try:
                            with open(file_path, 'rb') as f:
                                cloudinary_data = self.cloudinary_service.upload_file_from_bytes(
                                    file_content=f.read(),
                                    folder=f"generated_images/{user_id}",
                                    filename=file_path.name,
                                    validate_aspect_ratio=True  # Validate for social media
                                )
                                if cloudinary_data:
                                    cloudinary_url = cloudinary_data["secure_url"]
                                    logger.info("☁️ Image uploaded to Cloudinary: %s", cloudinary_url)
                        except Exception as e:
                            logger.warning("Cloudinary upload failed for %s: %s", file_path.name, str(e))
                    
                    # Create asset record
                    asset_id = str(uuid.uuid4())
                    asset_data = {
                        "asset_id": asset_id,
                        "user_id": user_id,
                        "file_path": str(file_path),
                        "storage_url": image_url,
                        "cloudinary_url": cloudinary_url,
                        "file_name": f"variation_{idx}.png",
                        "file_size_bytes": file_size,
                        "content_type": "image/png",
                        "asset_type": AssetType.GENERATED_IMAGE,
                        "generation_source": GenerationSource.AI,
                        "generation_prompt": image_prompt,
                        "campaign_idea": campaign_idea,
                        "variation_number": idx,
                        "model_used": self.image_model
                    }
                    
                    await self.asset_repo.create(asset_data)
                    asset_ids.append(asset_id)
                    logger.info("✅ Saved asset %s for user %s (variation %d)", asset_id, user_id, idx)
                    
                except Exception as asset_error:
                    logger.error("❌ Failed to save asset for %s: %s", image_url, str(asset_error))
                    # Continue with other assets even if one fails
            
            logger.info("🎉 Image generation complete! Generated %d images, saved %d assets", len(image_paths), len(asset_ids))
            return {
                "success": True,
                "image_prompt": image_prompt,
                "image_paths": image_paths,
                "asset_ids": asset_ids,
                "count": len(image_paths)
            }
            
        except Exception as e:
            logger.error("❌ Campaign image generation failed: %s", str(e))
            logger.error("Error type: %s", type(e).__name__)
            import traceback
            logger.error("Traceback: %s", traceback.format_exc())
            return {
                "success": False,
                "error": "Generation failed",
                "message": str(e)
            }


# Singleton instance
_image_service: Optional[ImageGenerationService] = None


def get_image_generation_service() -> ImageGenerationService:
    """Get or create the image generation service instance."""
    global _image_service
    if _image_service is None:
        _image_service = ImageGenerationService()
    return _image_service
