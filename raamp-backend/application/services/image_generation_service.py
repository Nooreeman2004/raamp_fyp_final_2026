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

from config import Config
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
    PROMPT_GENERATOR_SYSTEM_PROMPT = """You are an expert AI image prompt engineer for social media marketing.

Your ONLY job is to ENHANCE the user's request into a detailed image generation prompt.

## ABSOLUTE RULES (violating any of these is a failure):

### RULE 1 — NEVER CHANGE THE SUBJECT
- The specific objects, food, products, or scenes the user mentions are LOCKED.
- If the user says "pasta and bakery items" the image MUST show pasta and bakery items.
- If the user says "bubble tea" the image MUST show bubble tea.
- NEVER replace or omit the user's stated subjects with generic lifestyle props, accessories, or brand aesthetics.
- Brand context provides STYLE hints only. It does NOT override the subject matter.

### RULE 2 — SUBJECT FIRST, STYLE SECOND
- Structure: [user's exact subject/scene] + [composition/lighting] + [optional brand color atmosphere].
- Brand colors may tint background, lighting, or overlays ONLY — not replace the subject.
- "Cozy" or "minimal" brand themes apply to atmosphere, not to what objects appear.

### RULE 3 — ENHANCE, DON'T REPLACE
- Keep the user's exact wording for the main subject.
- Add photographic detail: lighting angle, texture, composition, depth of field.
- Output length: 100-200 words.

## OUTPUT FORMAT:
Output ONLY the image generation prompt. No explanations. No preamble. Just the prompt."""

    def __init__(self):
        """Initialize the image generation service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
        self.image_model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-3.1-flash-image-preview")
        self.imagen_model = os.getenv("GEMINI_IMAGEN_MODEL", "imagen-4.0-generate-001")
        self.output_folder = Config.GENERATED_IMAGES_DIR
        self.output_folder.mkdir(exist_ok=True)
        self.asset_repo = AssetRepository()
        self.cloudinary_service = CloudinaryService()
        
        logger.info(f"ImageGenerationService initialized - Text: {self.text_model}, Image: {self.image_model}, Imagen: {self.imagen_model}")
    
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
        
        palette: list[str] = []
        if brand_context.get("brand_colors"):
            try:
                palette = [str(c).strip() for c in (brand_context.get("brand_colors") or []) if str(c).strip()]
            except Exception:
                palette = []
        if not palette:
            if brand_context.get("primary_color"):
                palette.append(str(brand_context["primary_color"]).strip())
            if brand_context.get("secondary_color"):
                palette.append(str(brand_context["secondary_color"]).strip())
        palette_str = ", ".join([p for p in palette if p])
        if palette_str:
            sections.append(
                "COLOR CONSTRAINT (HARD RULE): "
                f"Dominant palette MUST be: {palette_str}. "
                "Avoid off-brand palettes (except black/white/neutral grays) unless explicitly required by the campaign request."
            )
        
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
    ) -> Dict[str, Any]:
        """
        Generate a detailed image prompt using Gemini.
        
        Args:
            campaign_idea: User's campaign description
            brand_context: Brand information from database
            
        Returns:
            Dict with:
            - image_prompt: str
            - logo_used: bool
            - logo_warning: Optional[str]
        """
        try:
            brand_section = self._build_brand_context_section(brand_context)
            logo_url = brand_context.get("brand_logo_url") or brand_context.get("logo_url")
            logo_used = False
            logo_warning = None

            # Support relative URLs stored by our API (e.g. /api/static/...).
            # We need a resolvable absolute URL for server-side fetching.
            if isinstance(logo_url, str) and logo_url.startswith("/"):
                public_base = os.getenv("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")
                logo_url = f"{public_base}{logo_url}"
            
            user_message = f"""## USER'S EXACT IMAGE REQUEST — SUBJECT IS LOCKED, DO NOT CHANGE IT:
"{campaign_idea}"

{brand_section}

## YOUR TASK:
Enhance the user's request above into a detailed image generation prompt.
The subject "{campaign_idea[:150]}" MUST appear in the image exactly as described.
Only add lighting, composition, texture, and atmospheric style details.
Do NOT replace, omit, or generalise the user's stated objects or scene."""

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
                        logo_used = True
                        logger.info("✅ Logo fetched (%d bytes, %s) — passing to Gemini", len(img_bytes), mime)
                    else:
                        logger.warning("⚠️ Logo fetch failed (%d) — proceeding text-only", logo_resp.status_code)
                        logo_warning = (
                            "Logo could not be loaded from the stored URL — images were generated without visual brand reference. "
                            "Check your brand profile logo URL."
                        )
                        contents = [self.PROMPT_GENERATOR_SYSTEM_PROMPT + "\n\n" + user_message]
                except Exception as logo_err:
                    logger.warning("⚠️ Could not fetch logo: %s — proceeding text-only", logo_err)
                    logo_warning = (
                        "Logo could not be loaded from the stored URL — images were generated without visual brand reference. "
                        "Check your brand profile logo URL."
                    )
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
                return {
                    "image_prompt": (
                        f"Professional social media marketing image for: {campaign_idea}. "
                        "Modern design, high-quality photography, vibrant colors, "
                        "clean composition, suitable for Instagram feed posts (1:1 ratio), "
                        "eye-catching and scroll-stopping."
                    ),
                    "logo_used": logo_used,
                    "logo_warning": logo_warning,
                }
            
            logger.info("Image prompt generated successfully")
            return {"image_prompt": image_prompt, "logo_used": logo_used, "logo_warning": logo_warning}
            
        except Exception as e:
            logger.error("Image prompt generation failed: %s", str(e))
            # Return a fallback prompt instead of raising so generation can still proceed
            return {
                "image_prompt": (
                    f"Professional social media marketing image for: {campaign_idea}. "
                    "High-quality photography, vibrant colors, clean composition for Instagram."
                ),
                "logo_used": False,
                "logo_warning": (
                    "Logo could not be loaded from the stored URL — images were generated without visual brand reference. "
                    "Check your brand profile logo URL."
                )
                if (brand_context.get("brand_logo_url") or brand_context.get("logo_url"))
                else None,
            }
    
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
                        response_modalities=["IMAGE"]
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
                    # Log what we actually got for debugging
                    part_types = [type(p).__name__ + (f"(text={p.text[:40]!r})" if hasattr(p, 'text') and p.text else "") for p in response.candidates[0].content.parts]
                    logger.warning("⚠️ [Strategy 1] No inline_data in response (attempt %d) — parts: %s", attempt, part_types)
                else:
                    logger.warning("⚠️ [Strategy 1] No candidates in response (attempt %d)", attempt)
            except Exception as e:
                logger.warning("⚠️ [Strategy 1] failed: %s (attempt %d)", str(e), attempt)

            # --- Strategy 2: Imagen API generate_images ---
            try:
                response = self.client.models.generate_images(
                    model=self.imagen_model,
                    prompt=image_prompt,
                    config=types.GenerateImagesConfig(
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
        """Helper to save a GeneratedImage object returned by generate_images."""
        try:
            # SDK v1+: GeneratedImage.image is an Image object with image_bytes + save()
            if hasattr(image_obj, 'image') and image_obj.image is not None:
                img = image_obj.image
                # Preferred: use the Image.save() helper
                if hasattr(img, 'save'):
                    img.save(filename)
                    return True
                # Fallback: raw bytes
                if hasattr(img, 'image_bytes') and img.image_bytes:
                    with open(filename, 'wb') as f:
                        f.write(img.image_bytes)
                    return True
            # Legacy: direct image_bytes on the object
            if hasattr(image_obj, 'image_bytes') and image_obj.image_bytes:
                with open(filename, 'wb') as f:
                    f.write(image_obj.image_bytes)
                return True
            # Legacy: PIL Image via .image.save
            if hasattr(image_obj, 'save'):
                image_obj.save(filename)
                return True
            logger.warning("⚠️ Unknown image object type: %s attrs=%s", type(image_obj), [a for a in dir(image_obj) if not a.startswith('_')])
            return False
        except Exception as e:
            logger.error("❌ Failed to save image object: %s", str(e))
            return False
    
    async def generate_images(
        self, 
        image_prompt: str, 
        campaign_id: Optional[str] = None,
        count: int = 3,
        aspect_ratio: str = "1:1",
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
            tasks.append(self._generate_single_image(image_prompt, filename, aspect_ratio=aspect_ratio))
        
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
        user_id: str,
        aspect_ratio: str = "1:1",
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
            prompt_result = self.generate_image_prompt(campaign_idea, brand_context)
            image_prompt = str(prompt_result.get("image_prompt", "")).strip()
            logo_used = bool(prompt_result.get("logo_used", False))
            logo_warning = prompt_result.get("logo_warning")
            logger.info("✅ Image prompt generated: %s...", image_prompt[:100])
            
            # Step 2: Generate 3 images
            logger.info("🖼️ Step 2: Generating 3 images using %s", self.image_model)
            campaign_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_paths = await self.generate_images(
                image_prompt,
                campaign_id,
                count=3,
                aspect_ratio=aspect_ratio,
            )
            
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
                "count": len(image_paths),
                "logo_used": logo_used,
                "logo_warning": logo_warning,
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
