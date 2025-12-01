"""
RAAMP Vector Store Module
=========================
ChromaDB-based vector store for the RAAMP Assistant RAG pipeline.
Handles collection creation, upserting, and semantic search.
"""

import os
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class ChromaVectorStore:
    """
    ChromaDB Vector Store for RAAMP FAQ retrieval.
    Provides persistent storage and semantic search capabilities.
    """
    
    COLLECTION_NAME = "raamp_faq_collection"
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the ChromaDB vector store.
        
        Args:
            persist_directory: Directory for persistent storage.
                             Defaults to VECTOR_STORE_PATH from .env
        """
        if persist_directory is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            persist_directory = os.path.join(
                base_dir,
                os.getenv("VECTOR_STORE_PATH", "data/vector_store_data")
            )
        
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        self.collection = None
        print(f"✅ ChromaDB initialized at: {self.persist_directory}")
    
    def get_or_create_collection(self, 
                                  collection_name: str = None,
                                  embedding_dimension: int = None) -> chromadb.Collection:
        """
        Get existing collection or create a new one.
        
        Args:
            collection_name: Name of the collection. Defaults to COLLECTION_NAME
            embedding_dimension: Dimension of embeddings (for metadata only)
            
        Returns:
            ChromaDB Collection object
        """
        if collection_name is None:
            collection_name = self.COLLECTION_NAME
        
        if embedding_dimension is None:
            embedding_dimension = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536"))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={
                "description": "RAAMP FAQ embeddings for RAG retrieval",
                "embedding_dimension": embedding_dimension,
                "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            }
        )
        
        print(f"✅ Collection '{collection_name}' ready (count: {self.collection.count()})")
        return self.collection
    
    def upsert_embeddings(self,
                          ids: List[str],
                          embeddings: List[List[float]],
                          documents: List[str],
                          metadatas: List[Dict[str, Any]] = None) -> None:
        """
        Upsert embeddings into the collection.
        
        Args:
            ids: List of unique IDs for each embedding
            embeddings: List of embedding vectors
            documents: List of document texts
            metadatas: Optional list of metadata dictionaries
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        if metadatas is None:
            metadatas = [{} for _ in ids]
        
        # ChromaDB upsert handles both insert and update
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"✅ Upserted {len(ids)} embeddings to collection")
    
    def search(self,
               query_embedding: List[float],
               n_results: int = None,
               where: Dict[str, Any] = None,
               include: List[str] = None) -> Dict[str, Any]:
        """
        Search the collection using a query embedding.
        
        Args:
            query_embedding: The embedding vector to search with
            n_results: Number of results to return
            where: Optional filter conditions
            include: What to include in results (documents, metadatas, distances)
            
        Returns:
            Dictionary containing search results
        """
        if self.collection is None:
            self.get_or_create_collection()
        
        if n_results is None:
            n_results = int(os.getenv("DEFAULT_N_RESULTS", "5"))
        
        if include is None:
            include = ["documents", "metadatas", "distances"]
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
            include=include
        )
        
        return results
    
    def search_by_text(self,
                       query_text: str,
                       embedding_func,
                       n_results: int = None,
                       similarity_threshold: float = None) -> List[Dict[str, Any]]:
        """
        Search using text query (requires embedding function).
        
        Args:
            query_text: Text query to search for
            embedding_func: Function to generate embeddings
            n_results: Number of results to return
            similarity_threshold: Minimum similarity score (optional)
            
        Returns:
            List of formatted search results
        """
        if similarity_threshold is None:
            similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))
        
        # Generate embedding for query
        query_embedding = embedding_func(query_text)
        
        # Search
        results = self.search(query_embedding, n_results=n_results)
        
        # Format results
        formatted_results = []
        if results and results.get("ids") and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                distance = results["distances"][0][i] if results.get("distances") else 0
                # ChromaDB uses L2 distance, convert to similarity
                similarity = 1 / (1 + distance)
                
                if similarity >= similarity_threshold:
                    formatted_results.append({
                        "id": doc_id,
                        "document": results["documents"][0][i] if results.get("documents") else "",
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": distance,
                        "similarity": similarity
                    })
        
        return formatted_results
    
    def delete_collection(self, collection_name: str = None) -> None:
        """Delete a collection."""
        if collection_name is None:
            collection_name = self.COLLECTION_NAME
        
        try:
            self.client.delete_collection(collection_name)
            self.collection = None
            print(f"✅ Collection '{collection_name}' deleted")
        except Exception as e:
            print(f"⚠️ Could not delete collection: {e}")
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the current collection."""
        if self.collection is None:
            return {"error": "No collection loaded"}
        
        return {
            "name": self.collection.name,
            "count": self.collection.count(),
            "metadata": self.collection.metadata
        }
    
    def list_collections(self) -> List[str]:
        """List all collections in the database."""
        collections = self.client.list_collections()
        return [c.name for c in collections]
    
    def reset(self) -> None:
        """Reset the entire database (use with caution!)."""
        self.client.reset()
        self.collection = None
        print("✅ Database reset complete")


def main():
    """Test the vector store functionality."""
    print("🚀 Testing ChromaDB Vector Store...")
    print("=" * 50)
    
    store = ChromaVectorStore()
    collection = store.get_or_create_collection()
    
    info = store.get_collection_info()
    print(f"\n📊 Collection Info: {info}")
    
    print("\n✅ Vector store test complete!")


if __name__ == "__main__":
    main()
