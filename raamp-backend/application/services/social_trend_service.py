
# Application Layer - Social Trend Service
import logging
from typing import List, Dict, Tuple
from infrastructure.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class SocialTrendService:
    """
    Service for deriving social trend signals using semantic analysis.
    Proxies social engagement by analyzing keyword intent and alignment with platform cultures.
    """
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
        
        # Platform Archetypes - distinct cultural concepts for each platform
        # These act as "anchors" in vector space
        self.PLATFORM_ARCHETYPES = {
            "instagram": [
                "aesthetic", "visual", "lifestyle", "beauty", "fashion", "photo", 
                "influencer", "travel", "food", "moment", "story", "reel"
            ],
            "facebook": [
                "community", "family", "news", "local event", "group", "discussion", 
                "article", "politics", "older generation", "marketplace"
            ],
            "google": [
                "information", "how to", "price", "review", "definition", "analysis", 
                "research", "solution", "product specs", "technical"
            ],
            "tiktok": [
                "challenge", "viral", "sound", "dance", "hack", "short video",
                "entertainment", "funny", "trend", "gen z"
            ]
        }
        
        # Pre-compute archetype embeddings (cached in memory)
        self.archetype_embeddings = {}
        self._initialize_archetypes()

    def _initialize_archetypes(self):
        """Compute average embedding for each platform's keywords"""
        if not self.embedding_service.client:
            logger.warning("Embedding service not available, skipping archetype init.")
            return

        for platform, keywords in self.PLATFORM_ARCHETYPES.items():
            # Get embeddings for all keywords
            vectors = self.embedding_service.get_embeddings(keywords)
            if vectors:
                # Average them to get a "centroid" for the platform culture
                import numpy as np
                centroid = np.mean(vectors, axis=0).tolist()
                self.archetype_embeddings[platform] = centroid

    def analyze_platform_bias(self, keyword: str) -> Dict[str, float]:
        """
        Determine which platform a keyword is most suited for based on semantic similarity.
        Returns a dictionary of scores {platform: score (0-1)}.
        """
        if not self.archetype_embeddings:
            # Fallback heuristic if embeddings fail
            return self._heuristic_bias(keyword)

        keyword_vec = self.embedding_service.get_embeddings([keyword])[0]
        
        scores = {}
        for platform, archetype_vec in self.archetype_embeddings.items():
            # Cosine similarity
            similarity = self.embedding_service.cosine_similarity(keyword_vec, archetype_vec)
            # Normalize/Scale: Cosine sim usually 0.7-0.9 for loosely related text, 
            # we want to stretch differences.
            # Map 0.7 -> 0.2, 0.85 -> 0.9
            adjusted_score = max(0, (similarity - 0.7) * 5) 
            scores[platform] = min(1.0, round(adjusted_score, 2))
            
        return scores

    def _heuristic_bias(self, keyword: str) -> Dict[str, float]:
        """Fallback simple keyword matching"""
        k = keyword.lower()
        scores = {"google": 0.5, "instagram": 0.3, "facebook": 0.2}
        
        if any(w in k for w in ["how", "what", "price", "buy", "review"]):
            scores["google"] += 0.3
        if any(w in k for w in ["outfit", "style", "look", "photo", "pic"]):
            scores["instagram"] += 0.4
        if any(w in k for w in ["group", "event", "local", "market"]):
            scores["facebook"] += 0.3
            
        # Normalize
        total = sum(scores.values())
        return {k: round(v/total, 2) for k, v in scores.items()}

    def generate_hashtags(self, keywords: List[str], count: int = 10) -> List[str]:
        """
        Convert related search queries into hashtags.
        Filters out navigational queries and formats them.
        """
        hashtags = set()
        for kw in keywords:
            # Simple cleaning
            clean = kw.lower().replace(" ", "").replace("-", "")
            if len(clean) > 20 or len(clean) < 3:
                continue
                
            # Add variations
            hashtags.add(f"#{clean}")
            
            # If multi-word, adding camelCase variant could be good, but simple is safer
        
        return list(hashtags)[:count]

    def compute_social_trend_score(self, interest_growth: float, platform_scores: Dict[str, float]) -> float:
        """
        Compute an aggregate social trend score.
        High growth + high visual platform affinity (Insta/TikTok) = High Social Score.
        """
        # We value viral platforms higher for "Social Trends"
        viral_factor = max(
            platform_scores.get("tiktok", 0), 
            platform_scores.get("instagram", 0)
        )
        
        # Social Score is combination of Google Velocity (proxy for overall interest) 
        # and Viral Platform Fit.
        # If something is growing fast AND fits Instagram -> High Social Score.
        score = (interest_growth * 0.4) + (viral_factor * 100 * 0.6)
        
        return min(100.0, max(0.0, score))
