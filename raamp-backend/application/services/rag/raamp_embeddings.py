"""
RAAMP Embeddings Module
=======================
Generates embeddings for FAQ chunks using OpenAI's embedding model.
Saves embeddings to a pickle file and upserts to Pinecone vector store.
"""

import os
import json
import pickle
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from dotenv import load_dotenv
import openai
from pinecone import Pinecone, ServerlessSpec

# Load environment variables
load_dotenv()


@dataclass
class EmbeddedChunk:
    """Represents a chunk with its embedding."""
    id: str
    content: str
    embedding: List[float]
    metadata: Dict[str, Any]


class RAAMPEmbeddingGenerator:
    """
    Generates embeddings for RAAMP FAQ chunks using OpenAI's API
    and handles Pinecone upserts.
    """
    
    def __init__(self):
        """Initialize the embedding generator with OpenAI and Pinecone settings."""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large")
        # Pinecone index is 3072 dimensions for text-embedding-3-large by default, 
        # but the user might have configured 1024.
        # Check if dimensions env var is set, otherwise default to model default (3072) or user pref.
        # Note: text-embedding-3-large native is 3072. 
        self.dimensions = int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "3072"))
        
        # Pinecone settings
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not self.pinecone_api_key:
            print("⚠️ PINECONE_API_KEY not found. Pinecone operations will be skipped.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Initialize Pinecone
        self.pc = None
        if self.pinecone_api_key:
            self.pc = Pinecone(api_key=self.pinecone_api_key)
        
        print(f"✅ Embedding generator initialized")
        print(f"   Model: {self.model}")
        print(f"   Dimensions: {self.dimensions}")
        if self.pc:
            print(f"   Pinecone: Enabled (Index: {self.pinecone_index_name})")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            # text-embedding-3-large supports 'dimensions' parameter to truncate
            response = self.client.embeddings.create(
                model=self.model,
                input=text,
                dimensions=self.dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call
            
        Returns:
            List of embedding vectors
        """
        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"   Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch,
                    dimensions=self.dimensions
                )
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                print(f"❌ Error in batch {batch_num}: {e}")
                raise
        
        return all_embeddings
    
    def load_chunks(self, chunks_path: str = None) -> List[Dict[str, Any]]:
        """
        Load chunks from the JSON file.
        
        Args:
            chunks_path: Path to chunks JSON file
            
        Returns:
            List of chunk dictionaries
        """
        if chunks_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            chunks_path = os.path.join(base_dir, "data", "embeddings_data", "raamp_chunks.json")
            # Fallback to old path if not found (based on previous file view logic)
            if not os.path.exists(chunks_path):
                 chunks_path = os.path.join(base_dir, "data", "raamp_chunks.json")

        
        if not os.path.exists(chunks_path):
            raise FileNotFoundError(f"Chunks file not found: {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return data.get("chunks", [])
    
    def process_chunks(self, chunks: List[Dict[str, Any]]) -> List[EmbeddedChunk]:
        """
        Process chunks and generate embeddings for each.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            List of EmbeddedChunk objects
        """
        print(f"\n📝 Processing {len(chunks)} chunks...")
        
        # Extract content texts for batch embedding
        texts = [chunk["content"] for chunk in chunks]
        
        # Generate embeddings in batch
        print("🔄 Generating embeddings...")
        embeddings = self.generate_embeddings_batch(texts)
        
        # Create EmbeddedChunk objects
        embedded_chunks = []
        for chunk, embedding in zip(chunks, embeddings):
            # Ensure we have a valid list of keywords/related_modules for metadata
            keywords = chunk.get("keywords", [])
            if isinstance(keywords, list):
                keywords = ", ".join(keywords)
                
            related_modules = chunk.get("related_modules", [])
            if isinstance(related_modules, list):
                related_modules = ", ".join(related_modules)
            
            embedded_chunk = EmbeddedChunk(
                id=chunk["id"],
                content=chunk["content"],
                embedding=embedding,
                metadata={
                    "question": chunk.get("question", ""),
                    "answer": chunk.get("answer", ""),
                    "category": chunk.get("category", ""),
                    "related_modules": related_modules,
                    "user_level": chunk.get("user_level", ""),
                    "keywords": keywords,
                    "chunk_type": chunk.get("chunk_type", "faq"),
                    "created_at": chunk.get("created_at", datetime.utcnow().isoformat())
                }
            )
            embedded_chunks.append(embedded_chunk)
        
        print(f"✅ Generated embeddings for {len(embedded_chunks)} chunks")
        return embedded_chunks
    
    def save_embeddings(self, 
                        embedded_chunks: List[EmbeddedChunk], 
                        output_path: str = None) -> str:
        """
        Save embedded chunks to a pickle file.
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects
            output_path: Path for output file
            
        Returns:
            Path to saved file
        """
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            embeddings_dir = os.path.join(
                base_dir,
                os.getenv("EMBEDDINGS_PATH", "data/embeddings_data")
            )
            os.makedirs(embeddings_dir, exist_ok=True)
            output_path = os.path.join(embeddings_dir, "raamp_faq_chunks_complete.pkl")
        
        # Prepare data for saving
        save_data = {
            "created_at": datetime.utcnow().isoformat(),
            "model": self.model,
            "dimensions": self.dimensions,
            "total_chunks": len(embedded_chunks),
            "chunks": [
                {
                    "id": ec.id,
                    "content": ec.content,
                    "embedding": ec.embedding,
                    "metadata": ec.metadata
                }
                for ec in embedded_chunks
            ]
        }
        
        with open(output_path, 'wb') as f:
            pickle.dump(save_data, f)
        
        print(f"✅ Saved embeddings locally to: {output_path}")
        return output_path
    
    def upsert_to_pinecone(self, embedded_chunks: List[EmbeddedChunk]):
        """
        Upsert embeddings to Pinecone.
        
        Args:
            embedded_chunks: List of EmbeddedChunk objects
        """
        if not self.pc or not self.pinecone_index_name:
            print("⚠️ Pinecone not configured. Skipping upsert.")
            return

        print(f"\n🌲 Preparing to upsert {len(embedded_chunks)} vectors to Pinecone index '{self.pinecone_index_name}'...")
        
        # Check if index exists, if not create it (optional, usually users create it beforehand)
        try:
            # We assume index exists or user wants us to fail if it doesn't, 
            # to avoid creating unintended indexes.
            index = self.pc.Index(self.pinecone_index_name)
            
            # Prepare vectors for upsert
            vectors = []
            for chunk in embedded_chunks:
                vectors.append({
                    "id": chunk.id,
                    "values": chunk.embedding,
                    "metadata": {
                        "content": chunk.content, # Storing content for retrieval
                        **chunk.metadata
                    }
                })
            
            # Batch upsert
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                try:
                    index.upsert(vectors=batch)
                    total_upserted += len(batch)
                    print(f"   Upserted batch {i//batch_size + 1} ({len(batch)} vectors)")
                except Exception as e:
                    print(f"❌ Error upserting batch {i}: {e}")
            
            print(f"✅ Successfully upserted {total_upserted} vectors to Pinecone")
            
        except Exception as e:
            print(f"❌ Error connecting to or upserting to Pinecone: {e}")

    def load_embeddings(self, embeddings_path: str = None) -> Dict[str, Any]:
        """
        Load embeddings from pickle file.
        
        Args:
            embeddings_path: Path to embeddings pickle file
            
        Returns:
            Dictionary containing embedding data
        """
        if embeddings_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            embeddings_path = os.path.join(
                base_dir,
                os.getenv("EMBEDDINGS_PATH", "data/embeddings_data"),
                "raamp_faq_chunks_complete.pkl"
            )
        
        if not os.path.exists(embeddings_path):
            raise FileNotFoundError(f"Embeddings file not found: {embeddings_path}")
        
        with open(embeddings_path, 'rb') as f:
            return pickle.load(f)


def generate_query_embedding(text: str) -> List[float]:
    """
    Utility function to generate embedding for a query.
    Can be used by the retriever module.
    
    Args:
        text: Query text
        
    Returns:
        Embedding vector
    """
    generator = RAAMPEmbeddingGenerator()
    return generator.generate_embedding(text)


def main():
    """Main function to run the embedding generation process."""
    print("🚀 Starting RAAMP Embedding Generation...")
    print("=" * 50)
    
    try:
        generator = RAAMPEmbeddingGenerator()
        
        # Load chunks
        chunks = generator.load_chunks()
        print(f"📚 Loaded {len(chunks)} chunks")
        
        # Generate embeddings
        embedded_chunks = generator.process_chunks(chunks)
        
        # Save to pickle file (local backup)
        generator.save_embeddings(embedded_chunks)
        
        # Upsert to Pinecone
        generator.upsert_to_pinecone(embedded_chunks)
        
        print("\n✨ All operations completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Script failed: {e}")

if __name__ == "__main__":
    main()
