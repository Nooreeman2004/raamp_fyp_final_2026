
import asyncio
import time
import uuid
from datetime import datetime
from infrastructure.database.database import connect_to_mongo, get_database
from infrastructure.repositories.ab_test_repository import get_ab_test_repository

async def seed_data():
    await connect_to_mongo()
    db = get_database()
    repo = get_ab_test_repository()
    
    user_id = "perf_test_user@example.com"
    
    # Clean up old test data
    await db["ab_test_batches"].delete_many({"user_id": user_id})
    await db["ab_test_images"].delete_many({"user_id": user_id})
    
    print("Seeding 200 batches and 1000 images...")
    batches = []
    images = []
    
    for i in range(200):
        batch_id = str(uuid.uuid4())
        batches.append({
            "batch_id": batch_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        })
        for j in range(5):
            images.append({
                "image_id": str(uuid.uuid4()),
                "ab_test_batch_id": batch_id,
                "user_id": user_id,
                "composite_score": 8.5
            })
            
    await db["ab_test_batches"].insert_many(batches)
    await db["ab_test_images"].insert_many(images)
    print("Seeding complete.")
    
    # Measure performance of aggregation
    start_time = time.time()
    results = await repo.get_user_batches(user_id, limit=200)
    end_time = time.time()
    
    print(f"Aggregation query for 200 batches (1000 images) took: {(end_time - start_time) * 1000:.2f} ms")
    print(f"Total results: {len(results)}")
    if len(results) > 0:
        print(f"Sample image count: {results[0]['image_count']}")
    
    # Cleanup
    await db["ab_test_batches"].delete_many({"user_id": user_id})
    await db["ab_test_images"].delete_many({"user_id": user_id})

if __name__ == "__main__":
    asyncio.run(seed_data())
