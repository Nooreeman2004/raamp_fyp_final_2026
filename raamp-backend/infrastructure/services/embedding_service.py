
# Infrastructure Layer - Embedding Service
import logging
from typing import List, Dict, Union
import numpy as np

# Try to import openai, handle if not installed
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating and comparing text embeddings"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        self.model = "text-embedding-3-small" # Efficient and sufficient for keyword clustering
        
        if self.api_key and HAS_OPENAI:
            self.client = OpenAI(api_key=self.api_key)
        else:
            logger.warning("OpenAI API Key not found or openai package missing. Embedding service will be disabled/mocked.")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts using OpenAI"""
        if not self.client or not texts:
            # Fallback mock if no client (returns random vectors)
            logger.warning("Using mock embeddings (no OpenAI client)")
            return [np.random.rand(1536).tolist() for _ in texts]
            
        try:
            # Clean and truncate texts to avoid token limits
            cleaned_texts = [t[:8000] for t in texts]
            
            response = self.client.embeddings.create(
                input=cleaned_texts,
                model=self.model
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            # Fallback
            return [np.random.rand(1536).tolist() for _ in texts]

    def cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(v1)
            vec2 = np.array(v2)
            
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
                
            return float(np.dot(vec1, vec2) / (norm1 * norm2))
        except Exception:
            return 0.0
            
    def compute_similarity_batch(self, source_vec: List[float], candidate_vecs: List[List[float]]) -> List[float]:
        """Compute similarity between one source vector and many candidates efficiently"""
        try:
            source = np.array(source_vec)
            candidates = np.array(candidate_vecs)
            
            source_norm = np.linalg.norm(source)
            candidate_norms = np.linalg.norm(candidates, axis=1)
            
            # Avoid division by zero
            candidate_norms[candidate_norms == 0] = 1e-9
            if source_norm == 0:
                source_norm = 1e-9
                
            dot_products = np.dot(candidates, source)
            similarities = dot_products / (candidate_norms * source_norm)
            
            return similarities.tolist()
        except Exception as e:
            logger.error(f"Error in batch similarity: {str(e)}")
            return [0.0] * len(candidate_vecs)
