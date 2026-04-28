"""
Video Generation Service
========================
AI-powered service for generating standard videos using Google Gemini Veo 3.1.
Generates various video types (horizontal, square) for different social media platforms.
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


class VideoGenerationService:
    """
    Service for generating AI-powered videos for social media.
    
    Uses Google Gemini to:
    1. Generate detailed video prompts from campaign ideas + brand context
    2. Generate videos using Veo 3.1 (horizontal 16:9 or square 1:1)
    """
    
    # System prompt for generating video scripts
    VIDEO_SYSTEM_PROMPT = """You are an expert video content creator and brand storyteller.

## ABSOLUTE RULES (violating any of these is a failure):

### RULE 1 — NEVER CHANGE THE SUBJECT
- The specific objects, food, products, scenes, or people the user mentions are LOCKED.
- If the user says "pasta being cooked" the video MUST show pasta being cooked.
- NEVER replace the user's stated subjects with generic props, lifestyle imagery, or brand aesthetics.
- Brand context provides STYLE hints only. It does NOT override the subject matter.

### RULE 2 — SUBJECT FIRST, STYLE SECOND
- Lead the prompt with the user's exact subject/scene, then layer in style.
- Brand colors/aesthetic apply to lighting, overlays, and end cards ONLY.

### RULE 3 — ENHANCE, DON'T REPLACE
- Keep the user's exact wording for the main subject in the prompt.
- Add cinematic detail: camera angles, lighting, pacing, transitions, audio direction.

Your prompt MUST include:
- **Opening shot**: Hook/intro
- **Scene description**: setting, subjects, objects, lighting
- **Camera movements**: shots, angles (pan, zoom, tracking, static)
- **Sequence of events**: What happens throughout
- **Visual style**: Color grading, mood, atmosphere
- **Audio direction**: Music vibe, sound effects
- **Pacing**: Timing and rhythm
- **Closing**: CTA, logo, fade out

## VIDEO TYPES:
- **Horizontal (16:9)**: YouTube, Facebook, LinkedIn
- **Square (1:1)**: Instagram feed, Facebook feed

## OUTPUT FORMAT:
Write a production-ready video prompt (200-350 words). Output ONLY the prompt. No meta-text."""

    def __init__(self):
        """Initialize the video generation service."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        self.client = genai.Client(api_key=self.api_key)
        self.text_model = os.getenv("GEMINI_TEXT_MODEL", "gemini-1.5-flash")
        self.video_model = os.getenv("VEO_MODEL", "veo-3.1-generate-preview")
        self.output_folder = Config.GENERATED_VIDEOS_DIR
        self.output_folder.mkdir(exist_ok=True)
        self.asset_repo = AssetRepository()
        self.cloudinary_service = CloudinaryService()
        
        logger.info(f"VideoGenerationService initialized - Text: {self.text_model}, Video: {self.video_model}")
    
    def _build_brand_context_section(self, brand_context: Dict[str, Any]) -> str:
        """Build the brand context section for the video prompt generator."""
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
            sections.append(f"Brand Color Palette (HEX): {', '.join(palette[:6])} (use for set design, overlays, end card)")
        
        if brand_context.get("tagline"):
            sections.append(f"Brand Tagline: {brand_context['tagline']}")
        
        if brand_context.get("brand_logo_url"):
            sections.append(
                f"Brand Logo: {brand_context['brand_logo_url']} (MUST show logo/end-card or watermark; do not invent logos)"
            )
            
        if brand_context.get("specialties"):
            sections.append(f"Specialties: {', '.join(brand_context['specialties'])}")
        
        if not sections:
            return "Brand Context: Create professional video content suitable for social media."
        
        return "## BRAND ASSETS PROVIDED:\n" + "\n".join(f"- {s}" for s in sections)
    
    def generate_video_prompt(
        self, 
        user_input: str, 
        brand_context: Optional[Dict[str, Any]] = None,
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        Generate a detailed video prompt using Gemini.
        
        Args:
            user_input: User's campaign description or video idea
            brand_context: Optional brand information from database
            aspect_ratio: "16:9" (horizontal) or "1:1" (square)
            
        Returns:
            Detailed video production prompt optimized for Veo 3.1
        """
        try:
            brand_section = ""
            if brand_context:
                brand_section = self._build_brand_context_section(brand_context)
            
            user_message = f"""## USER'S EXACT VIDEO REQUEST — SUBJECT IS LOCKED, DO NOT CHANGE IT:
"{user_input}"

{brand_section}

## VIDEO SPECIFICATIONS:
Aspect Ratio: {aspect_ratio}

## YOUR TASK:
Enhance the user's request above into a detailed video production prompt ({aspect_ratio}).
The subject "{user_input[:150]}" MUST appear in the video exactly as described.
Only add camera work, lighting, pacing, transitions, and atmosphere.
Do NOT replace or omit the user's stated objects or scene."""
            
            logger.info("Generating video prompt with Gemini")
            
            response = self.client.models.generate_content(
                model=self.text_model,
                contents=f"{self.VIDEO_SYSTEM_PROMPT}\n\n{user_message}",
                config=types.GenerateContentConfig(
                    temperature=0.9,
                    max_output_tokens=1000
                )
            )
            
            video_prompt = response.text.strip()
            
            logger.info("Video prompt generated successfully")
            return video_prompt
            
        except Exception as e:
            logger.error("Video prompt generation failed: %s", str(e))
            raise ValueError(f"Failed to generate video prompt: {str(e)}")
    
    def generate_single_video(
        self, 
        video_prompt: str, 
        filename: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8
    ) -> Optional[str]:
        """
        Generate one video using Veo 3.1.
        
        Args:
            video_prompt: Detailed prompt for video generation
            filename: Output filename (will be saved as .mp4)
            aspect_ratio: "16:9" (horizontal) or "1:1" (square)
            duration_seconds: Video duration (default 8 seconds)
            
        Returns:
            File path if successful, None otherwise
        """
        try:
            # Validate duration (Veo 3.1 Fast supports 4-8 seconds only)
            if duration_seconds < 4 or duration_seconds > 8:
                logger.warning(f"Duration {duration_seconds}s out of range. Clamping to 4-8 seconds.")
                duration_seconds = max(4, min(8, duration_seconds))
            
            logger.info(f"🎬 Generating Video: {filename} ({duration_seconds}s)")
            
            # Ensure filename has .mp4 extension
            if not filename.endswith('.mp4'):
                filename = f"{filename}.mp4"
            
            # Start video generation
            operation = self.client.models.generate_videos(
                model=self.video_model,
                prompt=video_prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio=aspect_ratio,
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
                logger.info(f"  Waiting for video {filename}... ({elapsed_time}s elapsed)")
                time.sleep(poll_interval)
                elapsed_time += poll_interval
                operation = self.client.operations.get(operation)
            
            if not operation.done:
                logger.error(f"❌ Video generation timed out after {max_wait_time}s")
                return None
            
            # Check if operation was successful
            if operation.error:
                logger.error(f"❌ Video generation failed: {operation.error}")
                return None
            
            # Save video
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
            
            logger.info(f"✅ Video saved as {filename} (Size: {len(video_bytes)} bytes)")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Failed to generate video {filename}: {str(e)}")
            import traceback
            logger.error(f"   Traceback:\n{traceback.format_exc()}")
            return None
    
    async def generate_single_video_async(
        self, 
        video_prompt: str, 
        filename: str,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8
    ) -> Optional[str]:
        """
        Async wrapper for generate_single_video.
        
        Allows parallel video generation without blocking.
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            self.generate_single_video, 
            video_prompt, 
            filename, 
            aspect_ratio,
            duration_seconds
        )
    
    async def generate_videos(
        self, 
        video_prompt: str, 
        campaign_id: Optional[str] = None,
        count: int = 3,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Generate multiple video variations in parallel.
        
        Args:
            video_prompt: Detailed prompt for video generation
            campaign_id: Optional ID to namespace the videos
            count: Number of variations to generate (default 3)
            aspect_ratio: "16:9" (horizontal) or "1:1" (square)
            duration_seconds: Video duration (default 8 seconds)
            
        Returns:
            List of file paths for successfully generated videos
        """
        if campaign_id:
            output_dir = self.output_folder / campaign_id
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_folder / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {count} video variations to {output_dir}")
        
        # Generate videos in parallel
        tasks = []
        for i in range(count):
            filename = str(output_dir / f"video_variation_{i+1}.mp4")
            tasks.append(self.generate_single_video_async(
                video_prompt, filename, aspect_ratio, duration_seconds
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None values and exceptions
        successful_videos = [
            r for r in results 
            if r is not None and not isinstance(r, Exception)
        ]
        
        logger.info(f"Successfully generated {len(successful_videos)}/{count} videos")
        
        return successful_videos
    
    def generate_videos_sync(
        self, 
        video_prompt: str, 
        output_folder: Optional[str] = None,
        count: int = 3,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Generate multiple video variations sequentially (synchronous version).
        
        Useful for simple scripts or when async is not needed.
        
        Args:
            video_prompt: Detailed prompt for video generation
            output_folder: Custom output folder (defaults to generated_videos/)
            count: Number of variations to generate (default 3)
            aspect_ratio: "16:9" (horizontal) or "1:1" (square)
            duration_seconds: Video duration (default 8 seconds)
            
        Returns:
            List of file paths for successfully generated videos
        """
        if output_folder:
            output_dir = Path(output_folder)
        else:
            # Use timestamp as fallback
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = self.output_folder / timestamp
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating {count} video variations to {output_dir}")
        
        results = []
        for i in range(count):
            filename = str(output_dir / f"video_variation_{i+1}.mp4")
            print(f"\nGenerating Video {i+1}/{count}...")
            result = self.generate_single_video(video_prompt, filename, aspect_ratio, duration_seconds)
            if result:
                results.append(result)
        
        logger.info(f"Successfully generated {len(results)}/{count} videos")
        
        return results
    
    async def save_videos_as_assets(
        self,
        video_paths: List[str],
        user_id: str,
        video_prompt: str,
        campaign_idea: Optional[str] = None,
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8
    ) -> List[str]:
        """
        Save generated videos as reusable assets in MongoDB.
        
        Args:
            video_paths: List of file paths to generated videos
            user_id: User identifier for asset ownership
            video_prompt: The prompt used to generate the videos
            campaign_idea: Original campaign idea from user
            aspect_ratio: Video aspect ratio
            duration_seconds: Duration of the videos
            
        Returns:
            List of asset IDs
        """
        logger.info(f"💾 Saving {len(video_paths)} videos as assets for user {user_id}")
        asset_ids = []
        
        for idx, file_path in enumerate(video_paths, start=1):
            try:
                path = Path(file_path)
                file_size = path.stat().st_size if path.exists() else 0
                
                # Convert to URL format
                relative_path = path.relative_to(self.output_folder)
                url = f"/api/videos/{relative_path}".replace("\\", "/")
                
                # Upload to Cloudinary (optional but recommended for public access)
                cloudinary_url = None
                if self.cloudinary_service.is_available:
                    try:
                        with open(path, 'rb') as f:
                            cloudinary_data = self.cloudinary_service.upload_file_from_bytes(
                                file_content=f.read(),
                                folder=f"generated_videos/{user_id}",
                                filename=path.name,
                                validate_aspect_ratio=False  # Videos don't need Instagram ratio validation
                            )
                            if cloudinary_data:
                                cloudinary_url = cloudinary_data["secure_url"]
                                logger.info(f"☁️ Video uploaded to Cloudinary: {cloudinary_url}")
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
                    "asset_type": AssetType.GENERATED_VIDEO,
                    "generation_source": GenerationSource.AI,
                    "generation_prompt": video_prompt,
                    "campaign_idea": campaign_idea,
                    "variation_number": idx,
                    "model_used": self.video_model,
                    "aspect_ratio": aspect_ratio,
                    "duration_seconds": duration_seconds
                }
                
                await self.asset_repo.create(asset_data)
                asset_ids.append(asset_id)
                logger.info(f"✅ Saved video asset {asset_id} (variation {idx})")
                
            except Exception as e:
                logger.error(f"❌ Failed to save video asset {file_path}: {str(e)}")
                # Continue with other assets
        
        logger.info(f"✅ Saved {len(asset_ids)}/{len(video_paths)} videos as assets")
        return asset_ids


# Singleton instance for easy access
_video_service_instance = None

def get_video_generation_service() -> VideoGenerationService:
    """Get or create the singleton video generation service instance."""
    global _video_service_instance
    if _video_service_instance is None:
        _video_service_instance = VideoGenerationService()
    return _video_service_instance
