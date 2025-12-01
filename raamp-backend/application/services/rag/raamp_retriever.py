"""
RAAMP Retriever Module (LangChain Enhanced)
============================================
Semantic search and retrieval component using LangChain's retriever abstraction.
Provides efficient document retrieval from the ChromaDB vector store.
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Load environment variables
load_dotenv()


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
    LangChain-based retriever for the RAAMP FAQ knowledge base.
    Provides semantic search with configurable similarity thresholds.
    """
    
    def __init__(self, 
                 collection_name: str = "raamp_faq_collection",
                 persist_directory: str = None):
        """
        Initialize the retriever.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Path to ChromaDB storage
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.getenv(
            "VECTOR_STORE_PATH", 
            "data/vector_store_data"
        )
        
        # Configuration
        self.n_results = int(os.getenv("DEFAULT_N_RESULTS", "5"))
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
        
        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize Chroma vector store
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory
        )
        
        # Create LangChain retriever
        self.retriever = self.vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": self.n_results,
                "score_threshold": self.similarity_threshold
            }
        )
        
        print("✅ RAAMP Retriever initialized with LangChain")
        print(f"   Collection: {self.collection_name}")
        print(f"   Top K: {self.n_results}, Threshold: {self.similarity_threshold}")
    
    def retrieve(self, 
                 query: str, 
                 n_results: int = None,
                 filter_category: str = None) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: User's question
            n_results: Number of results to return (overrides default)
            filter_category: Optional category filter
            
        Returns:
            List of RetrievedDocument objects
        """
        k = n_results or self.n_results
        
        # Use similarity search with scores for relevance information
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=query,
            k=k,
            filter={"category": filter_category} if filter_category else None
        )
        
        retrieved_docs = []
        for doc, score in results:
            if score >= self.similarity_threshold:
                retrieved_docs.append(RetrievedDocument(
                    id=doc.metadata.get("id", "unknown"),
                    content=doc.page_content,
                    question=doc.metadata.get("question", ""),
                    answer=doc.metadata.get("answer", ""),
                    category=doc.metadata.get("category", "General"),
                    relevance_score=round(score, 4),
                    metadata=doc.metadata
                ))
        
        return retrieved_docs
    
    def retrieve_documents(self, query: str, n_results: int = None) -> List[Document]:
        """
        Retrieve LangChain Document objects directly.
        Useful for integration with LangChain chains.
        
        Args:
            query: User's question
            n_results: Number of results
            
        Returns:
            List of LangChain Document objects
        """
        k = n_results or self.n_results
        return self.vector_store.similarity_search(query, k=k)
    
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
        Get the underlying LangChain retriever for use in chains.
        
        Returns:
            LangChain VectorStoreRetriever
        """
        return self.retriever
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store collection."""
        try:
            collection = self.vector_store._collection
            return {
                "name": self.collection_name,
                "count": collection.count(),
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            return {"error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check the health of the retriever."""
        try:
            stats = self.get_collection_stats()
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
