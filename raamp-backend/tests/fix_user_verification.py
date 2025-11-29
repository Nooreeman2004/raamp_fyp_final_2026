"""Fix user verification status - set is_verified=True and remove from pending"""
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database.database import init_db
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.repositories.pending_verification_repository import PendingVerificationRepository
from infrastructure.database.models.user_model import UserModel


async def fix_user_verification(email: str):
    """Fix user verification status"""
    
    # Initialize database
    await init_db()
    
    user_repo = UserRepository()
    pending_repo = PendingVerificationRepository()
    
    # Check users collection
    user = await user_repo.find_by_email(email.lower())
    pending = await pending_repo.find_by_email(email.lower())
    
    if not user:
        print(f"❌ User {email} not found in users collection")
        if pending:
            print(f"   Found in pending_verifications - complete email verification first")
        return
    
    print(f"\n📋 Current Status for {email}:")
    print(f"   Username: {user.username}")
    print(f"   Is Verified: {user.is_verified}")
    print(f"   In Pending: {'Yes' if pending else 'No'}")
    
    needs_fix = False
    
    # Fix 1: Set is_verified=True if False
    if not user.is_verified:
        print(f"\n🔧 Fixing: Setting is_verified=True...")
        user_model = await UserModel.find_one(UserModel.email == email.lower())
        if user_model:
            user_model.is_verified = True
            await user_model.save()
            print(f"   ✅ Updated is_verified to True")
            needs_fix = True
        else:
            print(f"   ❌ Failed to find UserModel")
    
    # Fix 2: Delete pending verification if exists
    if pending:
        print(f"\n🔧 Fixing: Deleting pending verification...")
        success = await pending_repo.delete_by_email(email.lower())
        if success:
            print(f"   ✅ Deleted pending verification")
            needs_fix = True
        else:
            print(f"   ❌ Failed to delete pending verification")
    
    if needs_fix:
        print(f"\n✅ User {email} is now properly verified and can sign in!")
    else:
        print(f"\n✅ User {email} was already properly verified")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        email = input("Enter email to fix: ").strip()
    else:
        email = sys.argv[1]
    
    confirm = input(f"\nFix verification status for {email}? (yes/no): ").strip().lower()
    
    if confirm == 'yes':
        asyncio.run(fix_user_verification(email))
    else:
        print("Cancelled")
