import asyncio
from infrastructure.database.database import connect_to_mongo, init_db
from domain.entities.user import User

async def main():
    await connect_to_mongo()
    await init_db()
    users = await User.find_all().to_list()
    for u in users:
        print(f"User: {u.email}")
        
    print(f"Total users: {len(users)}")

asyncio.run(main())
