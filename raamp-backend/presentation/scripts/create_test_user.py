
import asyncio
import os
import sys

# Add parent dir to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database.database import connect_to_mongo, init_db
from infrastructure.database.models.user_model import UserModel

async def main():
    await connect_to_mongo()
    await init_db()
    
    email = "verify_test@raamp.ai"
    user = await UserModel.find_one(UserModel.email == email)
    
    if not user:
        user = UserModel(
            username="verify_test",
            email=email,
            password_hash="dummy_hash",
            is_verified=True,
            agreed_to_terms=True,
            profile_completed=True
        )
        await user.insert()
        print(f"✅ User created: {email}")
    else:
        print(f"✅ User already exists: {email}")

if __name__ == "__main__":
    asyncio.run(main())
