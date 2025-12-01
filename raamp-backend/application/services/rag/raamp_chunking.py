"""
RAAMP Chunking Module
=====================
Processes the faq.json file into individual Q&A chunks for the RAG pipeline.
Each FAQ entry becomes a separate chunk with metadata for retrieval.
"""

import json
import os
from typing import List, Dict, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FAQChunk:
    """Represents a single FAQ chunk for the vector store."""
    id: str
    question: str
    answer: str
    category: str
    content: str  # Combined Q&A for embedding
    related_modules: List[str]
    user_level: str
    keywords: List[str]
    chunk_type: str = "faq"
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary."""
        return asdict(self)


class FAQChunker:
    """
    Processes FAQ JSON data into chunks suitable for embedding and retrieval.
    Each FAQ entry becomes a self-contained chunk with question, answer, and metadata.
    """
    
    def __init__(self, faq_file_path: str = None):
        """
        Initialize the FAQChunker.
        
        Args:
            faq_file_path: Path to the faq.json file. Defaults to standard location.
        """
        if faq_file_path is None:
            # Default path relative to the backend directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            faq_file_path = os.path.join(base_dir, "data", "raw_data", "faq.json")
        
        self.faq_file_path = faq_file_path
        self.chunks: List[FAQChunk] = []
    
    def load_faq_data(self) -> Dict[str, Any]:
        """Load FAQ data from the JSON file."""
        if not os.path.exists(self.faq_file_path):
            raise FileNotFoundError(f"FAQ file not found at: {self.faq_file_path}")
        
        with open(self.faq_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def create_content_text(self, question: str, answer: str, category: str) -> str:
        """
        Create the combined content text for embedding.
        This format is optimized for semantic search.
        
        Args:
            question: The FAQ question
            answer: The FAQ answer
            category: The FAQ category
            
        Returns:
            Combined text for embedding
        """
        return f"Category: {category}\n\nQuestion: {question}\n\nAnswer: {answer}"
    
    def process_faq_entry(self, faq: Dict[str, Any]) -> FAQChunk:
        """
        Process a single FAQ entry into a chunk.
        
        Args:
            faq: Dictionary containing FAQ data
            
        Returns:
            FAQChunk object
        """
        question = faq.get("question", "")
        answer = faq.get("answer", "")
        category = faq.get("category", "General")
        
        content = self.create_content_text(question, answer, category)
        
        return FAQChunk(
            id=faq.get("id", f"FAQ_{len(self.chunks):04d}"),
            question=question,
            answer=answer,
            category=category,
            content=content,
            related_modules=faq.get("related_modules", []),
            user_level=faq.get("user_level", "Basic"),
            keywords=faq.get("keywords", [])
        )
    
    def chunk_faqs(self) -> List[FAQChunk]:
        """
        Process all FAQs from the JSON file into chunks.
        
        Returns:
            List of FAQChunk objects
        """
        data = self.load_faq_data()
        faqs = data.get("faqs", [])
        
        self.chunks = []
        for faq in faqs:
            chunk = self.process_faq_entry(faq)
            self.chunks.append(chunk)
        
        print(f"✅ Processed {len(self.chunks)} FAQ entries into chunks")
        return self.chunks
    
    def save_chunks(self, output_path: str = None) -> str:
        """
        Save processed chunks to a JSON file.
        
        Args:
            output_path: Path for output file. Defaults to data/embeddings_data/raamp_chunks.json
            
        Returns:
            Path to the saved file
        """
        if output_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            output_path = os.path.join(base_dir, "data", "embeddings_data", "raamp_chunks.json")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        chunks_data = {
            "total_chunks": len(self.chunks),
            "created_at": datetime.utcnow().isoformat(),
            "source": self.faq_file_path,
            "chunks": [chunk.to_dict() for chunk in self.chunks]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(self.chunks)} chunks to: {output_path}")
        return output_path
    
    def get_chunk_by_id(self, chunk_id: str) -> FAQChunk | None:
        """Get a specific chunk by its ID."""
        for chunk in self.chunks:
            if chunk.id == chunk_id:
                return chunk
        return None
    
    def get_chunks_by_category(self, category: str) -> List[FAQChunk]:
        """Get all chunks from a specific category."""
        return [chunk for chunk in self.chunks if chunk.category.lower() == category.lower()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the processed chunks."""
        if not self.chunks:
            return {"error": "No chunks processed yet"}
        
        categories = {}
        user_levels = {}
        
        for chunk in self.chunks:
            categories[chunk.category] = categories.get(chunk.category, 0) + 1
            user_levels[chunk.user_level] = user_levels.get(chunk.user_level, 0) + 1
        
        return {
            "total_chunks": len(self.chunks),
            "categories": categories,
            "user_levels": user_levels,
            "avg_content_length": sum(len(c.content) for c in self.chunks) // len(self.chunks)
        }


def main():
    """Main function to run the chunking process."""
    print("🚀 Starting RAAMP FAQ Chunking Process...")
    print("=" * 50)
    
    chunker = FAQChunker()
    chunks = chunker.chunk_faqs()
    
    # Print statistics
    stats = chunker.get_statistics()
    print("\n📊 Chunking Statistics:")
    print(f"   Total Chunks: {stats['total_chunks']}")
    print(f"   Categories: {stats['categories']}")
    print(f"   User Levels: {stats['user_levels']}")
    print(f"   Avg Content Length: {stats['avg_content_length']} chars")
    
    # Save chunks
    output_path = chunker.save_chunks()
    
    print("\n✅ Chunking complete!")
    return chunks


if __name__ == "__main__":
    main()
