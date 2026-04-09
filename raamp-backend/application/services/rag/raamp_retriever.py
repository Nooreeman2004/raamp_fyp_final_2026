"""
RAAMP Retriever Module (LangChain Enhanced)
============================================
Semantic search and retrieval component using LangChain's retriever abstraction.
Provides efficient document retrieval from the ChromaDB vector store.
Includes intelligent query preprocessing with fuzzy matching and marketing context.
"""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_core.documents import Document

from .raamp_vector_store import PineconeVectorStore
from .raamp_embeddings import RAAMPEmbeddingGenerator
from .query_preprocessor import QueryPreprocessor, ProcessedQuery

# Load environment variables
load_dotenv()


from cachetools import TTLCache

@dataclass
class RetrievedDocument:
    """Represents a retrieved document with metadata."""
    id: str
    content: str
    question: str
    answer: str
    category: str
    relevance_score: float
    metadata: Dict[str, Any]


class RAAMPRetriever:
    """
    Retriever for the RAAMP FAQ knowledge base using Pinecone.
    Provides semantic search with configurable similarity thresholds.
    Includes intelligent query preprocessing for better results.
    """
    
    # Simple LRU cache for embeddings to speed up repeated queries
    _embedding_cache = TTLCache(maxsize=100, ttl=3600)  # Cache 100 queries for 1 hour
    
    def __init__(self, 
                 use_preprocessing: bool = True):
        """
        Initialize the retriever.
        
        Args:
            use_preprocessing: Whether to use query preprocessing
        """
        self.use_preprocessing = use_preprocessing
        
        # Configuration
        self.n_results = int(os.getenv("DEFAULT_N_RESULTS", "4")) # Default to 4 for better speed
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
        
        # Initialize query preprocessor
        self.preprocessor = QueryPreprocessor() if use_preprocessing else None
        
        # Initialize Embedding Generator
        self.embedding_generator = RAAMPEmbeddingGenerator()
        
        # Initialize Pinecone vector store
        self.vector_store = PineconeVectorStore()
        
        print("✅ RAAMP Retriever initialized with Pinecone (Caching enabled)")
        print(f"   Top K: {self.n_results}, Threshold: {self.similarity_threshold}")
    
    def retrieve(self, 
                 query: str, 
                 n_results: int = None,
                 filter_category: str = None,
                 skip_preprocessing: bool = False) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User's question
            n_results: Number of results to return (overrides default)
            filter_category: Optional category filter
            skip_preprocessing: Skip query preprocessing
            
        Returns:
            List of RetrievedDocument objects
        """
        k = n_results or self.n_results
        
        # Preprocess query for better matching
        search_query = query
        processed: Optional[ProcessedQuery] = None
        
        if self.use_preprocessing and not skip_preprocessing:
            processed = self.preprocessor.preprocess(query)
            search_query = processed.expanded
        
        # Generate embedding (check cache first)
        if search_query in self._embedding_cache:
            query_embedding = self._embedding_cache[search_query]
        else:
            query_embedding = self.embedding_generator.generate_embedding(search_query)
            self._embedding_cache[search_query] = query_embedding
        
        # Build filter
        filter_dict = {}
        if filter_category:
            filter_dict["category"] = filter_category
            
        # Search Pinecone
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=k,
            filter_dict=filter_dict if filter_dict else None
        )
        
        retrieved_docs = []
        for match in results.get("matches", []):
            score = match.get("score", 0)
            if score >= self.similarity_threshold:
                metadata = match.get("metadata", {})
                retrieved_docs.append(RetrievedDocument(
                    id=match.get("id", "unknown"),
                    content=metadata.get("text", ""),
                    question=metadata.get("question", ""),
                    answer=metadata.get("answer", ""),
                    category=metadata.get("category", "General"),
                    relevance_score=round(score, 4),
                    metadata={
                        **metadata,
                        "query_processed": processed.cleaned if processed else query,
                        "query_intent": processed.intent if processed else "unknown"
                    }
                ))
        
        return retrieved_docs
    
    def retrieve_documents(self, query: str, n_results: int = None) -> List[Document]:
        """
        Retrieve LangChain Document objects directly.
        
        Args:
            query: User's question
            n_results: Number of results
            
        Returns:
            List of LangChain Document objects
        """
        docs = self.retrieve(query, n_results)
        return [
            Document(page_content=d.content, metadata=d.metadata)
            for d in docs
        ]
    
    def retrieve_with_context(self, 
                               query: str, 
                               n_results: int = None) -> str:
        """
        Retrieve documents and format as context string for LLM.
        
        Args:
            query: User's question
            n_results: Number of results
            
        Returns:
            Formatted context string
        """
        docs = self.retrieve(query, n_results)
        
        if not docs:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(
                f"[Document {i}]\n"
                f"Category: {doc.category}\n"
                f"Q: {doc.question}\n"
                f"A: {doc.answer}\n"
            )
        
        return "\n---\n".join(context_parts)
    
    def get_langchain_retriever(self):
        """
        Get a LangChain-compatible retriever interface.
        Note: Currently returns self since we implement retrieve_documents.
        """
        return self
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store index."""
        try:
            stats = self.vector_store.get_index_stats()
            return {
                "name": self.vector_store.index_name,
                "vector_count": stats.get("total_vector_count", 0),
                "dimension": stats.get("dimension", 0)
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the retriever."""
        try:
            stats = self.vector_store.get_index_stats()
            # Test query
            test_docs = self.retrieve("test", n_results=1)
            
            return {
                "status": "healthy",
                "collection_stats": stats,
                "test_query": "passed",
                "docs_found": len(test_docs)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


def main():
    """Test the retriever functionality."""
    print("🔍 Testing RAAMP Retriever (LangChain)...")
    print("=" * 50)
    
    retriever = RAAMPRetriever()
    
    # Health check
    health = retriever.health_check()
    print(f"\n📊 Health: {health['status']}")
    
    # Test queries
    test_queries = [
        "What is RAAMP?",
        "How do I sign up for an account?",
        "What is hyperlocal targeting?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*50}")
        print(f"🔍 Query: '{query}'")
        
        docs = retriever.retrieve(query)
        print(f"📚 Retrieved {len(docs)} documents:")
        
        for doc in docs:
            print(f"   - [{doc.category}] {doc.question[:50]}... (score: {doc.relevance_score})")
    
    print("\n✅ Retriever test complete!")


if __name__ == "__main__":
    main()
