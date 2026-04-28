"""
A/B Test Optimizer Use Case
============================
Business logic for analyzing and ranking restaurant marketing images.
"""

import hashlib
import logging
import uuid
from datetime import datetime
from functools import lru_cache
from typing import Any, Dict, List, Optional

from domain.entities.ab_test_image import (
    ImageAnalysisResult,
    ImageAnalysisScore,
    ContentType,
    ABTestBatch
)
from infrastructure.services.openai_vision_service import get_vision_service
from infrastructure.repositories.ab_test_repository import get_ab_test_repository
from domain.utils.scoring_logic import get_relevance_level, get_score_grade

logger = logging.getLogger(__name__)


class ABTestOptimizerUseCase:
    """
    Use case for A/B testing image optimization.
    
    Responsibilities:
    - Analyze uploaded images with OpenAI Vision
    - Cache results to avoid duplicate API calls
    - Rank images by composite score
    - Generate A/B test recommendations
    - Store results in database
    """
    
    def __init__(self):
        """Initialize use case with required dependencies"""
        self.vision_service = get_vision_service()
        self.repository = get_ab_test_repository()
    
    async def analyze_single_image(
        self,
        image_path: str,
        filename: str,
        user_id: str,
        image_url: Optional[str] = None,
        batch_id: Optional[str] = None
    ) -> ImageAnalysisResult:
        """
        Analyze a single image for restaurant marketing potential.
        
        Checks cache first to avoid duplicate API calls for the same file.
        
        Args:
            image_path: Local path to the image file
            filename: Original filename
            user_id: User who uploaded the image
            image_url: Optional public URL of the image
            batch_id: Optional batch ID if part of a batch analysis
            
        Returns:
            ImageAnalysisResult with scores and recommendations
            
        Raises:
            Exception: If analysis fails
        """
        logger.info("🔍 Analyzing image: %s for user: %s", filename, user_id)
        
        # Check cache by file hash (computed inline to avoid protected-member access)
        hasher = hashlib.md5(usedforsecurity=False)
        with open(image_path, "rb") as _fh:
            for _chunk in iter(lambda: _fh.read(8192), b""):
                hasher.update(_chunk)
        file_hash = hasher.hexdigest()
        
        cached = await self.repository.get_by_file_hash(file_hash, user_id)
        if cached:
            logger.info("⏭️  Using cached result for: %s", filename)
            # Update batch association so this image is findable under the new batch
            if batch_id and cached.get("ab_test_batch_id") != batch_id:
                await self.repository.images_collection.update_one(
                    {"image_id": cached["image_id"]},
                    {"$set": {"ab_test_batch_id": batch_id}}
                )
                cached["ab_test_batch_id"] = batch_id
            return self._dict_to_entity(cached)
        
        # Analyze with OpenAI Vision
        try:
            analysis_raw = await self.vision_service.analyze_image(image_path, filename)
            
            # Generate unique image ID
            image_id = str(uuid.uuid4())
            
            # Build entity
            result = ImageAnalysisResult(
                image_id=image_id,
                filename=filename,
                file_hash=file_hash,
                content_type=ContentType(analysis_raw["content_type"]),
                scores=ImageAnalysisScore(
                    restaurant_relevance=float(analysis_raw["restaurant_relevance"]),
                    viral_potential=float(analysis_raw["viral_potential"]),
                    aesthetic_quality=float(analysis_raw["aesthetic_quality"]),
                    composite_score=float(analysis_raw["composite_score"])
                ),
                why_good=analysis_raw["why_good"],
                why_bad=analysis_raw["why_bad"],
                recommendation=analysis_raw["recommendation"],
                relevance_level=get_relevance_level(float(analysis_raw["restaurant_relevance"])).value,
                score_grade=get_score_grade(float(analysis_raw["composite_score"])).value,
                user_id=user_id,
                image_url=image_url,
                ab_test_batch_id=batch_id,
                created_at=datetime.utcnow()
            )
            
            # Save to database
            await self._save_analysis(result, image_path)
            
            logger.info("✅ Analysis complete: %s - Score: %s/10", filename, result.scores.composite_score)  # pylint: disable=no-member
            
            return result
            
        except (TypeError, ValueError, KeyError, OSError) as e:
            logger.error("❌ Failed to analyze %s: %s", filename, e)
            raise RuntimeError(f"Image analysis failed: {e}") from e
    
    async def analyze_batch(
        self,
        images: List[Dict[str, str]],
        user_id: str
    ) -> ABTestBatch:
        """
        Analyze multiple images as a batch and generate A/B test recommendations.
        
        Args:
            images: List of dicts with keys: 'path', 'filename', 'url' (optional)
            user_id: User who uploaded the images
            
        Returns:
            ABTestBatch with all analyzed images and recommendations
            
        Raises:
            ValueError: If fewer than 2 images provided
        """
        if len(images) < 2:
            raise ValueError("A/B testing requires at least 2 images")
        
        if len(images) > 5:
            raise ValueError("Maximum 5 images allowed per batch")
        
        logger.info("📊 Starting batch analysis of %d images for user: %s", len(images), user_id)
        
        # Generate batch ID
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        
        # Analyze each image
        results = []
        for img in images:
            try:
                result = await self.analyze_single_image(
                    image_path=img["path"],
                    filename=img["filename"],
                    user_id=user_id,
                    image_url=img.get("url"),
                    batch_id=batch_id
                )
                results.append(result)
            except (TypeError, ValueError, KeyError, OSError) as e:
                logger.error("❌ Failed to analyze %s: %s", img['filename'], e)
                # Continue with other images
        
        if len(results) < 2:
            raise RuntimeError("Failed to analyze enough images for A/B testing (need at least 2)")
        
        # Create batch entity
        batch = ABTestBatch(
            batch_id=batch_id,
            user_id=user_id,
            images=results,
            created_at=datetime.utcnow()
        )
        
        # Calculate recommendations
        batch.calculate_recommendations()
        
        # Save batch to database
        await self._save_batch(batch)
        
        logger.info("✅ Batch analysis complete: %s - %d images analyzed", batch_id, len(results))
        
        return batch
    
    async def get_batch(self, batch_id: str, user_id: str) -> Optional[ABTestBatch]:
        """
        Retrieve a previously analyzed batch.
        
        Args:
            batch_id: Batch identifier
            user_id: User ID (for access control)
            
        Returns:
            ABTestBatch or None
        """
        batch_doc = await self.repository.get_batch(batch_id)
        if not batch_doc or batch_doc["user_id"] != user_id:
            return None
        
        # Load images
        images_docs = await self.repository.get_batch_images(batch_id)
        images = [self._dict_to_entity(doc) for doc in images_docs]
        
        batch = ABTestBatch(
            batch_id=batch_doc["batch_id"],
            user_id=batch_doc["user_id"],
            images=images,
            created_at=batch_doc["created_at"],
            recommended_pair=tuple(batch_doc.get("recommended_pair", [])) if batch_doc.get("recommended_pair") else None,
            score_gap=batch_doc.get("score_gap")
        )
        
        return batch
    
    async def get_user_batches(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get all batches for a user (summary view).
        
        Args:
            user_id: User ID
            limit: Maximum results to return
            
        Returns:
            List of batch summaries enriched with image counts
        """
        # The repository now handles count enrichment via aggregation (fixes N+1)
        return await self.repository.get_user_batches(user_id, limit)

    async def get_user_batches_paginated(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Get paginated batches for a user.
        """
        return await self.repository.get_user_batches_paginated(user_id, skip, limit)
    
    def estimate_cost(self, num_images: int) -> Dict[str, Any]:
        """
        Estimate OpenAI API cost for analyzing images.
        
        Args:
            num_images: Number of images to analyze
            
        Returns:
            Cost estimate dictionary
        """
        cost_usd = self.vision_service.estimate_cost(num_images)
        
        return {
            "num_images": num_images,
            "estimated_cost_usd": round(cost_usd, 4),
            "cost_per_image_usd": 0.00765,
            "model": "gpt-4o"
        }
    
    async def _save_analysis(self, result: ImageAnalysisResult, local_path: str) -> None:
        """Save analysis result to database"""
        doc = {
            "image_id": result.image_id,
            "filename": result.filename,
            "file_hash": result.file_hash,
            "content_type": result.content_type.value,
            "restaurant_relevance": result.scores.restaurant_relevance,
            "viral_potential": result.scores.viral_potential,
            "aesthetic_quality": result.scores.aesthetic_quality,
            "composite_score": result.scores.composite_score,
            "why_good": result.why_good,
            "why_bad": result.why_bad,
            "recommendation": result.recommendation,
            "user_id": result.user_id,
            "image_url": result.image_url,
            "local_path": local_path,
            "created_at": result.created_at,
            "ab_test_batch_id": result.ab_test_batch_id
        }
        await self.repository.save_analysis(doc)
    
    async def _save_batch(self, batch: ABTestBatch) -> None:
        """Save batch to database"""
        doc = {
            "batch_id": batch.batch_id,
            "user_id": batch.user_id,
            "image_ids": [img.image_id for img in batch.images],
            "created_at": batch.created_at,
            "recommended_pair": list(batch.recommended_pair) if batch.recommended_pair else None,
            "score_gap": batch.score_gap
        }
        await self.repository.create_batch(doc)
    
    def _dict_to_entity(self, doc: Dict[str, Any]) -> ImageAnalysisResult:
        """Convert database document to domain entity"""
        return ImageAnalysisResult(
            image_id=doc["image_id"],
            filename=doc["filename"],
            file_hash=doc.get("file_hash"),
            content_type=ContentType(doc["content_type"]),
            scores=ImageAnalysisScore(
                restaurant_relevance=doc["restaurant_relevance"],
                viral_potential=doc["viral_potential"],
                aesthetic_quality=doc["aesthetic_quality"],
                composite_score=doc["composite_score"]
            ),
            why_good=doc["why_good"],
            why_bad=doc["why_bad"],
            recommendation=doc["recommendation"],
            user_id=doc["user_id"],
            image_url=doc.get("image_url"),
            created_at=doc["created_at"],
            ab_test_batch_id=doc.get("ab_test_batch_id"),
            relevance_level=doc.get("relevance_level") or get_relevance_level(float(doc["restaurant_relevance"])).value,
            score_grade=doc.get("score_grade") or get_score_grade(float(doc["composite_score"])).value,
        )


@lru_cache(maxsize=1)
def get_ab_optimizer_use_case() -> ABTestOptimizerUseCase:
    """
    Get or create singleton use case instance.
    
    Returns:
        ABTestOptimizerUseCase instance
    """
    return ABTestOptimizerUseCase()
