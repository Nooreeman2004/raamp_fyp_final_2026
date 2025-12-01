"""
RAAMP RAG Pipeline (LangChain Enhanced)
========================================
Standalone execution script for the complete RAAMP RAG pipeline.
Run once for document ingestion/indexing, then use the chatbot API.

Usage:
    python -m application.services.rag.raamp_pipeline
    python -m application.services.rag.raamp_pipeline --ingest
    python -m application.services.rag.raamp_pipeline --test
"""

import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List

# Add parent directories to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"🔷 {title}")
    print("=" * 60)


def print_step(step_num: int, total: int, description: str):
    """Print a step indicator."""
    print(f"\n📌 Step {step_num}/{total}: {description}")
    print("-" * 40)


def step_1_chunking() -> Dict[str, Any]:
    """Step 1: Process FAQ JSON into chunks."""
    print_step(1, 2, "Chunking FAQ Data")
    
    from application.services.rag.raamp_chunking import FAQChunker
    
    start_time = time.time()
    
    chunker = FAQChunker()
    chunks = chunker.chunk_faqs()
    output_path = chunker.save_chunks()
    
    stats = chunker.get_statistics()
    elapsed = time.time() - start_time
    
    print(f"   ✅ Processed {len(chunks)} FAQ entries")
    print(f"   📁 Output: {output_path}")
    print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    return {
        "status": "success",
        "chunks_count": len(chunks),
        "output_path": output_path,
        "statistics": stats,
        "elapsed_time": elapsed
    }


def step_2_ingest_to_vectorstore() -> Dict[str, Any]:
    """Step 2: Ingest chunks into ChromaDB using LangChain."""
    print_step(2, 2, "Ingesting to Vector Store (LangChain)")
    
    from langchain_openai import OpenAIEmbeddings
    from langchain_chroma import Chroma
    from langchain_core.documents import Document
    
    start_time = time.time()
    
    # Load chunks from embeddings_data directory (where chunker saves them)
    chunks_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "data", "embeddings_data", "raamp_chunks.json"
    )
    chunks_path = os.path.normpath(chunks_path)
    
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)
    
    chunks = chunks_data.get("chunks", [])
    print(f"   📄 Loaded {len(chunks)} chunks from {chunks_path}")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Prepare documents for LangChain
    documents = []
    for chunk in chunks:
        doc = Document(
            page_content=f"Q: {chunk['question']}\nA: {chunk['answer']}",
            metadata={
                "id": chunk["id"],
                "question": chunk["question"],
                "answer": chunk["answer"],
                "category": chunk.get("category", "General"),
                "keywords": ", ".join(chunk.get("keywords", [])),
                "user_level": chunk.get("user_level", "Basic")
            }
        )
        documents.append(doc)
    
    print(f"   📝 Prepared {len(documents)} documents for ingestion")
    
    # Get persist directory
    persist_dir = os.getenv("VECTOR_STORE_PATH", "data/vector_store_data")
    
    # Create ChromaDB with LangChain
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name="raamp_faq_collection",
        persist_directory=persist_dir
    )
    
    # Get collection stats
    collection_count = vector_store._collection.count()
    
    elapsed = time.time() - start_time
    
    print(f"   ✅ Ingested {collection_count} documents to ChromaDB")
    print(f"   📁 Persist directory: {persist_dir}")
    print(f"   ⏱️  Time: {elapsed:.2f}s")
    
    return {
        "status": "success",
        "documents_ingested": collection_count,
        "persist_directory": persist_dir,
        "elapsed_time": elapsed
    }


def run_ingestion_pipeline() -> Dict[str, Any]:
    """Run the document ingestion pipeline (chunk + ingest)."""
    print_header("RAAMP RAG Ingestion Pipeline")
    print(f"Started at: {datetime.now().isoformat()}")
    
    pipeline_start = time.time()
    results = {}
    
    try:
        # Step 1: Chunking
        results["chunking"] = step_1_chunking()
        
        # Step 2: Ingest to vector store
        results["ingestion"] = step_2_ingest_to_vectorstore()
        
        results["status"] = "success"
        
    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        results["status"] = "failed"
        results["error"] = str(e)
        import traceback
        traceback.print_exc()
    
    total_elapsed = time.time() - pipeline_start
    results["total_elapsed_time"] = total_elapsed
    
    # Print summary
    print_header("Ingestion Summary")
    print(f"   Status: {'✅ SUCCESS' if results['status'] == 'success' else '❌ FAILED'}")
    print(f"   Total Time: {total_elapsed:.2f}s")
    
    if results["status"] == "success":
        print(f"\n   📊 Results:")
        print(f"      - Chunks processed: {results['chunking']['chunks_count']}")
        print(f"      - Documents ingested: {results['ingestion']['documents_ingested']}")
    
    print(f"\n   Completed at: {datetime.now().isoformat()}")
    
    return results


def run_test_pipeline() -> Dict[str, Any]:
    """Test the RAG retrieval and generation."""
    print_header("RAAMP RAG Test Pipeline")
    
    from application.services.rag.raamp_retriever import RAAMPRetriever
    from application.services.rag.raamp_generation import RAAMPGenerator
    
    results = {}
    
    # Test Retriever
    print("\n📌 Testing Retriever...")
    print("-" * 40)
    
    try:
        retriever = RAAMPRetriever()
        health = retriever.health_check()
        print(f"   Health: {health['status']}")
        
        test_query = "What is RAAMP?"
        docs = retriever.retrieve(test_query, n_results=3)
        print(f"   Query: '{test_query}'")
        print(f"   Retrieved: {len(docs)} documents")
        
        for doc in docs:
            print(f"      - [{doc.category}] {doc.question[:40]}... (score: {doc.relevance_score})")
        
        results["retriever"] = {"status": "success", "docs_retrieved": len(docs)}
    except Exception as e:
        print(f"   ❌ Retriever Error: {e}")
        results["retriever"] = {"status": "failed", "error": str(e)}
    
    # Test Generator
    print("\n📌 Testing Generator...")
    print("-" * 40)
    
    try:
        generator = RAAMPGenerator()
        health = generator.health_check()
        print(f"   Health: {health['status']}")
        
        test_queries = [
            "What is RAAMP?",
            "How do I sign up?",
            "What is the capital of France?"  # Guardrail test
        ]
        
        for query in test_queries:
            response = generator.generate_response(query, n_context=3)
            answer_preview = response.answer[:100] + "..." if len(response.answer) > 100 else response.answer
            print(f"\n   Q: {query}")
            print(f"   A: {answer_preview}")
        
        results["generator"] = {"status": "success"}
    except Exception as e:
        print(f"   ❌ Generator Error: {e}")
        results["generator"] = {"status": "failed", "error": str(e)}
    
    return results


def run_chat_demo():
    """Run an interactive chat demo."""
    print_header("RAAMP Assistant Chat Demo")
    
    from application.services.rag.raamp_generation import RAMPAssistant
    
    assistant = RAMPAssistant(session_id="demo-session")
    
    demo_queries = [
        "Hi there!",
        "What is RAAMP?",
        "How can it help my restaurant?",
        "Tell me about geo-intent targeting"
    ]
    
    print("\n🤖 RAAMP Assistant Demo\n")
    
    for query in demo_queries:
        print(f"👤 User: {query}")
        result = assistant.ask(query)
        answer = result["answer"] if isinstance(result, dict) else result
        print(f"🤖 Assistant: {answer}\n")
        print("-" * 50)
    
    print(f"\n📊 Conversation length: {assistant.get_conversation_length()} messages")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAAMP RAG Pipeline")
    parser.add_argument("--ingest", action="store_true", help="Run ingestion pipeline (chunk + index)")
    parser.add_argument("--test", action="store_true", help="Test retriever and generator")
    parser.add_argument("--demo", action="store_true", help="Run chat demo")
    
    args = parser.parse_args()
    
    if args.ingest:
        run_ingestion_pipeline()
    elif args.test:
        run_test_pipeline()
    elif args.demo:
        run_chat_demo()
    else:
        # Default: run full ingestion + test
        print("Running full pipeline (ingestion + test)...")
        run_ingestion_pipeline()
        print("\n")
        run_test_pipeline()


if __name__ == "__main__":
    main()
