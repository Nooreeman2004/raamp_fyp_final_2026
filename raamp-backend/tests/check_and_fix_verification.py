"""Simple check of user status in MongoDB"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

async def check_user(email: str):
    """Check user status in both collections"""
    mongo_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    # Check users collection
    user = await db["users"].find_one({"email": email.lower()})
    
    # Check pending_verifications collection
    pending = await db["pending_verifications"].find_one({"email": email.lower()})
    
    print(f"\n{'='*70}")
    print(f"VERIFICATION STATUS CHECK FOR: {email}")
    print(f"{'='*70}\n")
    
    if user:
        print(f"✅ FOUND IN USERS COLLECTION:")
        print(f"   Username: {user.get('username')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Is Verified: {user.get('is_verified', False)}")
        print(f"   Created: {user.get('created_at')}")
        
        if not user.get('is_verified', False):
            print(f"\n⚠️  WARNING: User exists but is_verified=False!")
            print(f"   This is why you can't sign in.")
            print(f"   Need to fix: Set is_verified=True")
    else:
        print(f"❌ NOT FOUND IN USERS COLLECTION")
    
    print()
    
    if pending:
        print(f"⚠️  FOUND IN PENDING_VERIFICATIONS:")
        print(f"   Username: {pending.get('username')}")
        print(f"   Email: {pending.get('email')}")
        print(f"   OTP: {pending.get('verification_code')}")
        print(f"   Expires: {pending.get('code_expires_at')}")
        
        if user:
            print(f"\n❌ DATA INCONSISTENCY!")
            print(f"   User exists in BOTH collections (should only be in one)")
            print(f"   Need to delete from pending_verifications")
    else:
        print(f"✅ NOT IN PENDING_VERIFICATIONS (correct)")
    
    print(f"\n{'='*70}")
    print("DIAGNOSIS:")
    print(f"{'='*70}")
    
    if user and user.get('is_verified', False) and not pending:
        print("✅ User is properly verified - can sign in normally")
    elif user and not user.get('is_verified', False):
        print("⚠️  User exists but NOT verified")
        print("   Solution: Run fix script to set is_verified=True")
    elif pending and not user:
        print("⚠️  Still in pending verification")
        print("   Solution: Complete email verification with OTP code")
    elif user and pending:
        print("❌ Data inconsistency - user in both collections")
        print("   Solution: Run fix script to clean up")
    else:
        print("❌ No record found - need to sign up first")
    
    print(f"{'='*70}\n")
    
    client.close()
    
    # Return whether fix is needed
    return user and (not user.get('is_verified', False) or pending)


async def fix_user(email: str):
    """Fix user verification status"""
    mongo_uri = os.getenv("MONGODB_URI")
    client = AsyncIOMotorClient(mongo_uri)
    db = client["raamp_db"]
    
    print(f"\n🔧 FIXING VERIFICATION STATUS FOR: {email}\n")
    
    # Update user to is_verified=True
    result = await db["users"].update_one(
        {"email": email.lower()},
        {
            "$set": {
                "is_verified": True,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count > 0:
        print(f"✅ Set is_verified=True for user")
    else:
        print(f"⚠️  User not found or already verified")
    
    # Delete from pending_verifications
    result = await db["pending_verifications"].delete_one({"email": email.lower()})
    
    if result.deleted_count > 0:
        print(f"✅ Deleted pending verification record")
    else:
        print(f"ℹ️  No pending verification to delete")
    
    print(f"\n✅ Done! User {email} can now sign in.\n")
    
    client.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        email = input("Enter email to check: ").strip()
    else:
        email = sys.argv[1]
    
    needs_fix = asyncio.run(check_user(email))
    
    if needs_fix:
        fix = input("Do you want to fix this issue? (yes/no): ").strip().lower()
        if fix == 'yes':
            asyncio.run(fix_user(email))
            print("Verification fixed! Try signing in now.")
