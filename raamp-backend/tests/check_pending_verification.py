"""Quick script to check if pending verification exists for an email"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

async def check_pending_verification(email: str):
    """Check if pending verification exists"""
    mongo_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Check pending verifications collection
    pending = await db["pending_verifications"].find_one({"email": email.lower()})
    
    if pending:
        print(f"✅ Found pending verification for {email}")
        print(f"   Username: {pending.get('username')}")
        print(f"   OTP Code: {pending.get('verification_code')}")
        print(f"   Expires at: {pending.get('code_expires_at')}")
        print(f"   Sent at: {pending.get('code_sent_at')}")
        print(f"   Resend count: {pending.get('resend_count', 0)}")
    else:
        print(f"❌ No pending verification found for {email}")
        
        # Check if user already exists and is verified
        user = await db["users"].find_one({"email": email.lower()})
        if user:
            print(f"   User exists: {user.get('username')}")
            print(f"   Is verified: {user.get('is_verified', False)}")
            print(f"   → You need to sign in, not verify!")
        else:
            print(f"   → You need to sign up first to create a pending verification!")
    
    client.close()

if __name__ == "__main__":
    email = input("Enter email to check: ").strip()
    asyncio.run(check_pending_verification(email))
