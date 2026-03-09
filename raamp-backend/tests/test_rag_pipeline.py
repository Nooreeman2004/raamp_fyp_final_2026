"""
Test the RAG pipeline step by step
"""
import os
import time
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("Testing RAG Pipeline Components")
print("=" * 60)

# Test 1: Embeddings
print("\n1️⃣  Testing Embeddings...")
try:
    from application.services.rag.raamp_embeddings import RAAMPEmbeddingGenerator
    
    embedder = RAAMPEmbeddingGenerator()
    start = time.time()
    embedding = embedder.generate_embedding("What is RAAMP?")
    elapsed = time.time() - start
    print(f"✅ Embeddings working ({elapsed:.2f}s)")
    print(f"   Dimension: {len(embedding)}")
except Exception as e:
    print(f"❌ Embeddings failed: {e}")

# Test 2: Retriever
print("\n2️⃣  Testing Retriever...")
try:
    from application.services.rag.raamp_retriever import RAAMPRetriever
    
    start = time.time()
    retriever = RAAMPRetriever()
    elapsed = time.time() - start
    print(f"✅ Retriever initialized ({elapsed:.2f}s)")
    
    start = time.time()
    docs = retriever.retrieve("What is RAAMP?", n_results=3)
    elapsed = time.time() - start
    print(f"✅ Retrieved {len(docs)} documents ({elapsed:.2f}s)")
    
    if docs:
        print(f"   Top result: {docs[0].question[:50]}...")
        print(f"   Relevance: {docs[0].relevance_score}")
except Exception as e:
    print(f"❌ Retriever failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Generator (the slow part)
print("\n3️⃣  Testing Generator...")
try:
    from application.services.rag.raamp_generation import RAAMPGenerator
    
    start = time.time()
    generator = RAAMPGenerator()
    elapsed = time.time() - start
    print(f"✅ Generator initialized ({elapsed:.2f}s)")
    
    start = time.time()
    response = generator.generate_simple("What is RAAMP?")
    elapsed = time.time() - start
    print(f"✅ Response generated ({elapsed:.2f}s)")
    print(f"   Answer: {response[:100]}...")
except Exception as e:
    print(f"❌ Generator failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
