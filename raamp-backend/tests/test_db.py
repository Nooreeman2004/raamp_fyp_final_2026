import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def run_test():
    client = AsyncIOMotorClient(
        "mongodb+srv://username:password@ac-1oyk1hi-shard-00-00.vtcx7x1.mongodb.net/test?retryWrites=true&w=majority&tls=true"
    )
    db = client.get_database("your_db_name")
    collections = await db.list_collection_names()
    print(collections)

if __name__ == "__main__":
    asyncio.run(run_test())
