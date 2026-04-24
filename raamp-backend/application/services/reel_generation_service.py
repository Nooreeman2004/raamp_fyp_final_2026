"""
Instagram Reel Generation Service
==================================
AI-powered service for generating Instagram Reels using Google Gemini Veo 3.1.
Generates detailed Reel scripts optimized for short-form vertical video (9:16).
"""

import os
import asyncio
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from google import genai
from google.genai import types
from dotenv import load_dotenv

from config import Config
from infrastructure.repositories.asset_repository import AssetRepository
from infrastructure.database.models.asset_model import AssetType, GenerationSource
from application.services.cloudinary_service import CloudinaryService

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class ReelGenerationService:
    """
    Service for generating AI-powered Instagram Reels.
    
    Uses Google Gemini to:
    1. Generate detailed Reel scripts/prompts from campaign ideas + brand context
    2. Generate short-form vertical videos (8-15s, 9:16 aspect ratio) using Veo 3.1
    """
    
    # System prompt for generating Instagram Reel scripts
    REEL_SYSTEM_PROMPT = """You are an expert social media content creator for Instagram Reels.
The user will describe their idea. Your job is to write a detailed Reel script and prompt
optimized for short-form vertical video (9:16), 8-15 seconds long.

Your prompt MUST include:
- **Hook**: First 1-3 words to stop scrolling (critical!)
- **Scene description**: setting, subjects, objects, environment
- **Camera movements & angles**: vertical framing, dynamic shots (pan, zoom, tilt)
- **Action/motion**: sequence of events, what happens when
- **Visual effects / transitions**: cuts, fade, zoom effects, text animations
- **Audio direction**: music vibe (upbeat/calm/dramatic), sound effects, voiceover cues
- **Timing breakdown**: what happens at each second (0-2s, 2-5s, 5-8s)
- **CTA (Call-to-Action)**: engagement hook (like, comment, save, share, follow)
- **Text overlay suggestions**: captions, stickers, emojis that appear on screen

## REEL FORMULA FOR SUCCESS (4-8 seconds):
1. **0-1s**: HOOK - Stop the scroll immediately
2. **1-3s**: Setup - Show the main subject/product
3. **3-6s**: Value delivery - Show the benefit/transformation
4. **6-8s**: CTA - Tell them what to do next

## Rules:
- Keep it concise: under 250 words
- Format like a professional Reel production prompt
- Only write the prompt; do not generate video yet
- Use vertical framing language (9:16 aspect)
- Focus on fast-paced, engaging content
- Include trending audio suggestions when relevant
- Make it scroll-stopping and shareable

## OUTPUT FORMAT:
Write a detailed, production-ready video prompt that Veo 3.1 can use to generate the Reel.
Be specific about timing, visuals, and audio."""

    def __init__(self):
        """Initialize the Reel generation service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-3-flash-preview")
        self.video_model = os.getenv("VEO_MODEL", "veo-3.1-generate-preview")
        self.output_folder = Config.GENERATED_REELS_DIR
        self.output_folder.mkdir(exist_ok=True)
        self.asset_repo = AssetRepository()
        self.cloudinary_service = CloudinaryService()
        
        logger.info(f"ReelGenerationService initialized - Text: {self.text_model}, Video: {self.video_model}")
    
    def _build_brand_context_section(self, brand_context: Dict[str, Any]) -> str:
        """Build the brand context section for the Reel prompt generator."""
        sections = []
        
        if brand_context.get("business_name"):
            sections.append(f"Brand Name: {brand_context['business_name']}")
        
        if brand_context.get("business_type"):
            sections.append(f"Industry: {brand_context['business_type']}")
        
        if brand_context.get("tone_of_voice"):
            sections.append(f"Brand Tone: {brand_context['tone_of_voice']}")
        
        if brand_context.get("target_audience"):
            sections.append(f"Target Audience: {brand_context['target_audience']}")
        
        palette: list[str] = []
        try:
            palette = [str(c).strip() for c in (brand_context.get("brand_colors") or []) if str(c).strip()]
        except Exception:
            palette = []
        if not palette:
            if brand_context.get("primary_color"):
                palette.append(str(brand_context["primary_color"]).strip())
            if brand_context.get("secondary_color"):
                palette.append(str(brand_context["secondary_color"]).strip())
        if palette:
            sections.append(f"Brand Color Palette (HEX): {', '.join(palette[:6])} (use for overlays, props, end card)")
        
        if brand_context.get("tagline"):
            sections.append(f"Brand Tagline: {brand_context['tagline']}")
            
        if brand_context.get("brand_logo_url"):
            sections.append(
                f"Brand Logo: {brand_context['brand_logo_url']} (MUST show logo/end-card or watermark; do not invent logos)"
            )
            
        if brand_context.get("specialties"):
            sections.append(f"Specialties: {', '.join(brand_context['specialties'])}")
        
        if not sections:
            return "Brand Context: Create engaging Reel content suitable for Instagram."
        
        return "## BRAND ASSETS PROVIDED:\n" + "\n".join(f"- {s}" for s in sections)
    
    def generate_reel_prompt(
        self, 
        user_input: str, 
        brand_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a detailed Instagram Reel prompt using Gemini.
        
        Args:
            user_input: User's campaign description or Reel idea
            brand_context: Optional brand information from database
            
        Returns:
            Detailed Reel production prompt optimized for Veo 3.1
        """
        try:
            brand_section = ""
            if brand_context:
                brand_section = self._build_brand_context_section(brand_context)
            
            user_message = f"""{brand_section}

## USER REEL REQUEST:
{user_input}

## TASK:
Generate a detailed Instagram Reel production prompt (8-15 seconds, 9:16 aspect ratio) following all the requirements above."""
            
            logger.info("Generating Reel prompt with Gemini")
            
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=f"{self.REEL_SYSTEM_PROMPT}\n\n{user_message}",
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=800
                )
            )
            
            reel_prompt = response.text.strip()
            
            logger.info("Reel prompt generated successfully")
            return reel_prompt
            
        except Exception as e:
            logger.error("Reel prompt generation failed: %s", str(e))
            raise ValueError(f"Failed to generate Reel prompt: {str(e)}")
    
    def generate_single_reel(
        self, 
        reel_prompt: str, 
        filename: str,
        duration_seconds: int = 8
    ) -> Optional[str]:
        """
        Generate one Reel video (short-form 4-8s) using Veo 3.1.
        
        Args:
            reel_prompt: Detailed prompt for Reel generation
            filename: Output filename (will be saved as .mp4)
            duration_seconds: Video duration (4-8 seconds, Veo 3.1 Fast limit)
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            # Validate duration (Veo 3.1 Fast supports 4-8 seconds only)
            if duration_seconds < 4 or duration_seconds > 8:
                logger.warning(f"Duration {duration_seconds}s out of range. Clamping to 4-8 seconds.")
                duration_seconds = max(4, min(8, duration_seconds))
            
            logger.info(f"🎬 Generating Reel: {filename} ({duration_seconds}s)")
            
            # Ensure filename has .mp4 extension
            if not filename.endswith('.mp4'):
                filename = f"{filename}.mp4"
            
            # Start video generation
            operation = self.client.models.generate_videos(
                model=self.video_model,
                prompt=reel_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="9:16",
                    duration_seconds=str(duration_seconds),
                    number_of_videos=1,
                ),
            )
            
            logger.info(f"  Video generation started, operation: {operation.name}")
            
            # Poll until done
            max_wait_time = 300  # 5 minutes max
            elapsed_time = 0
            poll_interval = 10  # Check every 10 seconds
            
            while not operation.done and elapsed_time < max_wait_time:
                logger.info(f"  Waiting for Reel {filename}... ({elapsed_time}s elapsed)")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                operation = self.client.operations.get(operation)
            
            if not operation.done:
                logger.error(f"❌ Reel generation timed out after {max_wait_time}s")
                return None
            
            # Check if operation was successful
            if operation.error:
                logger.error(f"❌ Reel generation failed: {operation.error}")
                return None
            
            # Save video
            # For Veo, result contains the generated videos
            result = operation.result if hasattr(operation, 'result') else operation.response
            generated_video = result.generated_videos[0]
            
            # Use the download method to get video bytes
            logger.info(f"  Downloading video content for {filename}...")
            video_bytes = self.client.files.download(file=generated_video.video)
            
            if not video_bytes:
                logger.error(f"❌ Failed to download video bytes for {filename}")
                return None
                
            # Write bytes to file
            with open(filename, 'wb') as f:
                f.write(video_bytes)
            
            logger.info(f"✅ Reel saved as {filename} (Size: {len(video_bytes)} bytes)")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to generate Reel {filename}: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            return None
    
    async def generate_single_reel_async(
        self, 
        reel_prompt: str, 
        filename: str,
        duration_seconds: int = 8
    ) -> Optional[str]:
        """
        Async wrapper for generate_single_reel.
        
        Allows parallel Reel generation without blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.generate_single_reel, 
            reel_prompt, 
            filename, 
            duration_seconds
        )
    
    async def generate_reels(
        self, 
        reel_prompt: str, 
        campaign_id: Optional[str] = None,
        count: int = 3,
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Generate multiple Reel variations in parallel.
        
        Args:
            reel_prompt: Detailed prompt for Reel generation
            campaign_id: Optional ID to namespace the Reels
            count: Number of variations to generate (default 3)
            duration_seconds: Video duration (4-8 seconds, Veo 3.1 Fast limit)
            
        Returns:
            List of file paths for successfully generated Reels
        """
        if campaign_id:
            output_dir = self.output_folder / campaign_id
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_folder / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {count} Reel variations to {output_dir}")
        
        # Generate Reels in parallel
        tasks = []
        for i in range(count):
            filename = str(output_dir / f"reel_variation_{i+1}.mp4")
            tasks.append(self.generate_single_reel_async(reel_prompt, filename, duration_seconds))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None values and exceptions
        successful_reels = [
            r for r in results 
            if r is not None and not isinstance(r, Exception)
        ]
        
        logger.info(f"Successfully generated {len(successful_reels)}/{count} Reels")
        
        return successful_reels
    
    def generate_reels_sync(
        self, 
        reel_prompt: str, 
        output_folder: Optional[str] = None,
        count: int = 3,
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Generate multiple Reel variations sequentially (synchronous version).
        
        Useful for simple scripts or when async is not needed.
        
        Args:
            reel_prompt: Detailed prompt for Reel generation
            output_folder: Custom output folder (defaults to generated_reels/)
            count: Number of variations to generate (default 3)
            duration_seconds: Video duration (4-8 seconds, Veo 3.1 Fast limit)
            
        Returns:
            List of file paths for successfully generated Reels
        """
        if output_folder:
            output_dir = Path(output_folder)
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_folder / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {count} Reel variations to {output_dir}")
        
        results = []
        for i in range(count):
            filename = str(output_dir / f"reel_variation_{i+1}.mp4")
            print(f"\nGenerating Reel {i+1}/{count}...")
            result = self.generate_single_reel(reel_prompt, filename, duration_seconds)
            if result:
                results.append(result)
        
        logger.info(f"Successfully generated {len(results)}/{count} Reels")
        
        return results
    
    async def save_reels_as_assets(
        self,
        reel_paths: List[str],
        user_id: str,
        reel_prompt: str,
        campaign_idea: Optional[str] = None,
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Save generated reels as reusable assets in MongoDB.
        
        Args:
            reel_paths: List of file paths to generated reels
            user_id: User identifier for asset ownership
            reel_prompt: The prompt used to generate the reels
            campaign_idea: Original campaign idea from user
            duration_seconds: Duration of the reels
            
        Returns:
            List of asset IDs
        """
        logger.info(f"💾 Saving {len(reel_paths)} reels as assets for user {user_id}")
        asset_ids = []
        
        for idx, file_path in enumerate(reel_paths, start=1):
            try:
                path = Path(file_path)
                file_size = path.stat().st_size if path.exists() else 0
                
                # Convert to URL format
                relative_path = path.relative_to(self.output_folder)
                url = f"/api/reels/{relative_path}".replace("\\", "/")
                
                # Upload to Cloudinary (optional but recommended for public access)
                cloudinary_url = None
                if self.cloudinary_service.is_available:
                    try:
                        with open(path, 'rb') as f:
                            cloudinary_data = self.cloudinary_service.upload_file_from_bytes(
                                file_content=f.read(),
                                folder=f"generated_reels/{user_id}",
                                filename=path.name,
                                validate_aspect_ratio=False  # Reels don't need validation (already 9:16)
                            )
                            if cloudinary_data:
                                cloudinary_url = cloudinary_data["secure_url"]
                                logger.info(f"☁️ Reel uploaded to Cloudinary: {cloudinary_url}")
                    except Exception as e:
                        logger.warning(f"Cloudinary upload failed for {path.name}: {e}")
                
                # Create asset record
                asset_id = str(uuid.uuid4())
                asset_data = {
                    "asset_id": asset_id,
                    "user_id": user_id,
                    "file_path": str(path),
                    "storage_url": url,
                    "cloudinary_url": cloudinary_url,
                    "file_name": path.name,
                    "file_size_bytes": file_size,
                    "content_type": "video/mp4",
                    "asset_type": AssetType.GENERATED_REEL,
                    "generation_source": GenerationSource.AI,
                    "generation_prompt": reel_prompt,
                    "campaign_idea": campaign_idea,
                    "variation_number": idx,
                    "model_used": self.video_model,
                    "aspect_ratio": "9:16",
                    "duration_seconds": duration_seconds
                }
                
                await self.asset_repo.create(asset_data)
                asset_ids.append(asset_id)
                logger.info(f"✅ Saved reel asset {asset_id} (variation {idx})")
                
            except Exception as e:
                logger.error(f"❌ Failed to save reel asset {file_path}: {str(e)}")
                # Continue with other assets
        
        logger.info(f"✅ Saved {len(asset_ids)}/{len(reel_paths)} reels as assets")
        return asset_ids


# Singleton instance for easy access
_reel_service_instance = None

def get_reel_generation_service() -> ReelGenerationService:
    """Get or create the singleton Reel generation service instance."""
    global _reel_service_instance
    if _reel_service_instance is None:
        _reel_service_instance = ReelGenerationService()
    return _reel_service_instance
