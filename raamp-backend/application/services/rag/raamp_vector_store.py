"""
RAAMP Vector Store Module
=========================
Pinecone-based vector store for the RAAMP Assistant RAG pipeline.
Handles index connection, upserting, and semantic search.
"""

import os
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()


class PineconeVectorStore:
    """
    Pinecone Vector Store for RAAMP FAQ retrieval.
    Provides persistent cloud storage and semantic search capabilities.
    """
    
    INDEX_NAME = "raamp"
    
    def __init__(self):
        """
        Initialize the Pinecone vector store.
        Requires PINECONE_API_KEY in environment variables.
        """
        self.api_key = os.getenv("PINECONE_API_KEY")
        if not self.api_key:
            print("⚠️ PINECONE_API_KEY not found. Helper requires this for vector ops.")
        
        # Initialize Pinecone client
        self.pc = Pinecone(api_key=self.api_key)
        self.index = None
        self.index_name = os.getenv("PINECONE_INDEX_NAME", self.INDEX_NAME)
        
        print(f"✅ Pinecone client initialized")
    
    def get_or_create_index(self, dimension: int = 1024) -> Any:
        """
        Get existing index or create a new one.
        
        Args:
            dimension: Dimension of embeddings (default 1024 for text-embedding-3-large)
            
        Returns:
            Pinecone Index object
        """
        # Check if index exists
        existing_indexes = [i.name for i in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            print(f"🔄 Creating Pinecone index '{self.index_name}'...")
            try:
                self.pc.create_index(
                    name=self.index_name,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                # Wait for index to be ready
                while not self.pc.describe_index(self.index_name).status['ready']:
                    time.sleep(1)
                print(f"✅ Index '{self.index_name}' created successfully")
            except Exception as e:
                print(f"❌ Failed to create index: {e}")
                # We might continue if it was just a race condition
        
        self.index = self.pc.Index(self.index_name)
        return self.index
    
    def upsert_embeddings(self,
                          ids: List[str],
                          embeddings: List[List[float]],
                          documents: List[str],
                          metadatas: List[Dict[str, Any]] = None) -> None:
        """
        Upsert embeddings into the index.
        
        Args:
            ids: List of unique IDs for each embedding
            embeddings: List of embedding vectors
            documents: List of document texts (stored in metadata)
            metadatas: Optional list of metadata dictionaries
        """
        if self.index is None:
            self.get_or_create_index()
        
        if metadatas is None:
            metadatas = [{} for _ in ids]
            
        # Prepare vectors for Pinecone (id, values, metadata)
        vectors = []
        for i, doc_id in enumerate(ids):
            # Ensure metadata contains the text content for retrieval
            meta = metadatas[i].copy()
            meta["text"] = documents[i]
            
            vectors.append({
                "id": doc_id,
                "values": embeddings[i],
                "metadata": meta
            })
            
        # Batch upsert (Pinecone recommends batches of 100-200)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            print(f"   Upserted batch {i//batch_size + 1}")
            
        print(f"✅ Upserted {len(ids)} embeddings to Pinecone index '{self.index_name}'")
    
    def search(self,
               query_embedding: List[float],
               n_results: int = 5,
               filter_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Search the index using a query embedding.
        
        Args:
            query_embedding: The embedding vector to search with
            n_results: Number of results to return
            filter_dict: Optional metadata filter
            
        Returns:
            Dictionary containing search results
        """
        if self.index is None:
            self.get_or_create_index()
        
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                include_metadata=True,
                filter=filter_dict
            )
            return results
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return {"matches": []}
    
    def delete_index(self) -> None:
        """Delete the index."""
        try:
            self.pc.delete_index(self.index_name)
            self.index = None
            print(f"✅ Index '{self.index_name}' deleted")
        except Exception as e:
            print(f"⚠️ Could not delete index: {e}")
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get information about the current index."""
        if self.index is None:
            self.get_or_create_index()
            
        try:
            return self.index.describe_index_stats()
        except Exception:
            return {"error": "Could not fetch stats"}


def main():
    """Run the full embedding generation and upsert pipeline."""
    print("🚀 Starting RAAMP Vector Store Pipeline...")
    print("=" * 50)
    
    # 1. Initialize Components
    from .raamp_embeddings import RAAMPEmbeddingGenerator
    
    store = PineconeVectorStore()
    embedding_gen = RAAMPEmbeddingGenerator()
    
    # 2. Get/Create Index
    store.get_or_create_index()
    
    # 3. Load or Generate Embeddings
    try:
        # Try to load existing pickle first to save money/time
        data = embedding_gen.load_embeddings()
        print(f"📦 Loaded {len(data['chunks'])} existing embeddings from pickle.")
        
        chunk_ids = [c["id"] for c in data["chunks"]]
        embeddings = [c["embedding"] for c in data["chunks"]]
        documents = [c["content"] for c in data["chunks"]]
        metadatas = [c["metadata"] for c in data["chunks"]]
        
    except FileNotFoundError:
        print("⚠️ No existing embeddings found. Generating new ones...")
        chunks = embedding_gen.load_chunks()
        embedded_chunks = embedding_gen.process_chunks(chunks)
        embedding_gen.save_embeddings(embedded_chunks)
        
        chunk_ids = [c.id for c in embedded_chunks]
        embeddings = [c.embedding for c in embedded_chunks]
        documents = [c.content for c in embedded_chunks]
        metadatas = [c.metadata for c in embedded_chunks]

    # 4. Upsert to Pinecone
    print("\n📤 Upserting to Pinecone...")
    store.upsert_embeddings(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )
    
    # 5. Verify
    stats = store.get_index_stats()
    print(f"\n📊 Final Index Stats: {stats}")
    
    print("\n✅ Setup complete! RAAMP Assistant is ready.")


if __name__ == "__main__":
    main()
