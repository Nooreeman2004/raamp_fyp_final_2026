"""Quick test for MongoDB connection"""
import asyncio
from infrastructure.database.database import connect_to_mongo, close_mongo_connection

async def test():
    try:
        await connect_to_mongo()
        print("Connection test successful!")
        await close_mongo_connection()
    except Exception as e:
        print(f"Connection test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
