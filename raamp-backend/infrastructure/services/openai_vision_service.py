"""
OpenAI Vision Service
=====================
Infrastructure service for analyzing images using GPT-4o Vision API.
"""

import os
import json
import base64
import hashlib
import logging
import mimetypes
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAIVisionService:
    """Service for analyzing images with GPT-4o Vision API"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("OPENAI_API_KEY not found in environment")
            raise ValueError("OPENAI_API_KEY is required for A/B Optimizer")
        
        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o"
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 string using chunked reading to save memory.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Base64 encoded string
        """
        import io
        output = io.StringIO()
        with open(image_path, "rb") as f:
            # Read in chunks of 3072 bytes (multiple of 3 to avoid intermediate padding)
            for chunk in iter(lambda: f.read(3072), b""):
                output.write(base64.b64encode(chunk).decode('utf-8'))
        return output.getvalue()
    
    def _calculate_file_hash(self, image_path: str) -> str:
        """
        Calculate MD5 hash of image file for caching using chunked reading.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            MD5 hash string
        """
        md5_hash = hashlib.md5()
        with open(image_path, "rb") as f:
            # Read in 64KB chunks
            for chunk in iter(lambda: f.read(65536), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def analyze_image(self, image_path: str, filename: str) -> Dict[str, Any]:
        """
        Analyze a restaurant marketing image for A/B test suitability.
        
        Uses GPT-4o Vision to score:
        - Restaurant relevance (filters out non-restaurant content)
        - Viral potential (engagement likelihood)
        - Aesthetic quality (visual appeal)
        
        Args:
            image_path: Path to the image file on disk
            filename: Original filename for reference
            
        Returns:
            Dictionary with analysis results matching ImageAnalysisResult schema
            
        Raises:
            Exception: If OpenAI API call fails
        """
        logger.info(f"🔍 Analyzing image: {filename}")
        
        # Encode image
        base64_image = self._encode_image(image_path)
        file_hash = self._calculate_file_hash(image_path)
        
        # Construct prompt
        prompt = """You are an expert restaurant marketing analyst. Analyze this image for social media viral potential.

**YOUR TASK:**
1. **Content Type**: Is this food, poster/flyer, interior, menu, people, or OTHER (like random street photos)?
2. **Restaurant Relevance**: Score 0-10 how relevant this is to restaurant marketing
   - 0-3: Not restaurant related (street photos, random people, etc.)
   - 4-6: Somewhat related but weak
   - 7-8: Good restaurant content
   - 9-10: Perfect restaurant marketing material
3. **Viral Score**: Score 0-10 for viral/engagement potential (IF it's restaurant content)
4. **Aesthetic Score**: Score 0-10 for visual quality
5. **Final Composite**: Average of (relevance * 0.4 + viral * 0.35 + aesthetic * 0.25)

**RESPOND IN JSON FORMAT:**
```json
{
  "content_type": "food|poster|interior|menu|people|other",
  "restaurant_relevance": 0-10,
  "viral_potential": 0-10,
  "aesthetic_quality": 0-10,
  "composite_score": 0-10,
  "why_good": "2-3 bullet points of strengths",
  "why_bad": "2-3 bullet points of weaknesses or why it's not restaurant content",
  "recommendation": "Use/Don't use and why in one sentence"
}
```

**IMPORTANT:** If this is a street photo, random selfie, or non-restaurant content, give LOW restaurant_relevance score!"""
        
        try:
            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mimetypes.guess_type(image_path)[0] or 'image/jpeg'};base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            # Parse JSON response
            result = json.loads(content)
            
            # Normalize why_good and why_bad to strings if they're arrays
            # (OpenAI sometimes returns arrays instead of strings)
            if isinstance(result.get("why_good"), list):
                result["why_good"] = "\\n".join(f"• {item}" for item in result["why_good"])
            if isinstance(result.get("why_bad"), list):
                result["why_bad"] = "\\n".join(f"• {item}" for item in result["why_bad"])
            
            # Add metadata
            result["filename"] = filename
            result["file_hash"] = file_hash
            
            logger.info(f"✅ Analysis complete: {filename} - Type: {result['content_type']}, Score: {result['composite_score']}/10")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ OpenAI Vision API error for {filename}: {str(e)}")
            raise Exception(f"Failed to analyze image: {str(e)}")
    
    def estimate_cost(self, num_images: int) -> float:
        """
        Estimate API cost for analyzing images.
        
        GPT-4o Vision pricing (as of 2024):
        - High detail: ~$0.00765 per image
        
        Args:
            num_images: Number of images to analyze
            
        Returns:
            Estimated cost in USD
        """
        cost_per_image = 0.00765  # High detail mode
        return num_images * cost_per_image


# Singleton instance
_vision_service_instance: Optional[OpenAIVisionService] = None


def get_vision_service() -> OpenAIVisionService:
    """
    Get or create singleton OpenAI Vision service instance.
    
    Returns:
        OpenAIVisionService instance
    """
    global _vision_service_instance
    if _vision_service_instance is None:
        _vision_service_instance = OpenAIVisionService()
    return _vision_service_instance
