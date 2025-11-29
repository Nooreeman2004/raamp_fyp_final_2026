"""Diagnostic script to check user verification status"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.database import init_db
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository


async def check_user_status(email: str):
    """Check if user is in users or pending_verifications collection"""
    
    # Initialize database
    try:
        await init_db()
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print("Attempting to continue...")
    
    user_repo = UserRepository()
    pending_repo = PendingVerificationRepository()
    
    # Check users collection
    user = await user_repo.find_by_email(email.lower())
    if user:
        print(f"\n✅ FOUND IN USERS COLLECTION:")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Is Verified: {user.is_verified}")
        print(f"   Created At: {user.created_at}")
        print(f"   ID: {user.id}")
        
        if not user.is_verified:
            print(f"\n⚠️  WARNING: User exists but is_verified=False")
            print(f"   This should be True if you completed email verification!")
            print(f"\n   SOLUTION: Update is_verified to True manually:")
            print(f"   Run: python tests/fix_user_verification.py {email}")
    else:
        print(f"\n❌ NOT FOUND IN USERS COLLECTION")
    
    # Check pending_verifications collection
    pending = await pending_repo.find_by_email(email.lower())
    if pending:
        print(f"\n⚠️  FOUND IN PENDING_VERIFICATIONS COLLECTION:")
        print(f"   Email: {pending.email}")
        print(f"   Username: {pending.username}")
        print(f"   OTP Code: {pending.verification_code}")
        print(f"   Expires At: {pending.code_expires_at}")
        print(f"   Sent At: {pending.code_sent_at}")
        
        if user:
            print(f"\n❌ ERROR: User exists in BOTH collections!")
            print(f"   This is a data inconsistency issue.")
            print(f"   The pending verification should have been deleted.")
            print(f"\n   SOLUTION: Delete the pending verification:")
            print(f"   Run: python tests/fix_user_verification.py {email}")
    else:
        print(f"\n✅ NOT IN PENDING_VERIFICATIONS COLLECTION (correct)")
    
    print("\n" + "="*70)
    
    if user and user.is_verified:
        print("✅ STATUS: User is properly verified and can sign in")
    elif user and not user.is_verified:
        print("⚠️  STATUS: User exists but not verified - needs is_verified=True")
    elif pending:
        print("⚠️  STATUS: Still pending verification - complete email verification")
    else:
        print("❌ STATUS: No record found - need to sign up first")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = input("Enter email to check: ").strip()
    else:
        email = sys.argv[1]
    
    asyncio.run(check_user_status(email))
