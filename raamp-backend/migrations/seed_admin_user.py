"""
Seed Admin User Migration
==========================
Grant admin privileges to support staff.

SECURITY: This script should only be run locally or via secure deployment pipeline.
NEVER expose an API endpoint that grants admin access.

Usage:
    python migrations/seed_admin_user.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db
from infrastructure.database.models.user_model import UserModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ADMIN USERS: Add support staff emails here
ADMIN_EMAILS = [
    "malik.noor.eman@email.com",  # Primary admin
    "abdullah@gmail.com",         # Demo account (already has special privileges)
]


async def seed_admin_users():
    """Grant admin privileges to specified users."""
    await connect_to_mongo()
    await init_db()
    
    logger.info("🔐 Starting admin user seeding...")
    
    granted_count = 0
    not_found_count = 0
    already_admin_count = 0
    
    for email in ADMIN_EMAILS:
        user = await UserModel.find_one(UserModel.email == email)
        
        if not user:
            logger.warning(f"⚠️  User not found: {email}")
            not_found_count += 1
            continue
        
        if user.is_admin:
            logger.info(f"✓ Already admin: {email}")
            already_admin_count += 1
            continue
        
        # Grant admin privileges
        user.is_admin = True
        await user.save()
        
        logger.info(f"✅ Granted admin privileges: {email}")
        granted_count += 1
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("📊 ADMIN SEEDING SUMMARY")
    logger.info("="*60)
    logger.info(f"✅ Granted admin access: {granted_count}")
    logger.info(f"✓  Already admin: {already_admin_count}")
    logger.info(f"⚠️  Users not found: {not_found_count}")
    logger.info("="*60)
    
    if not_found_count > 0:
        logger.warning("\n⚠️  WARNING: Some admin users were not found in the database.")
        logger.warning("These users must register accounts before they can access admin features.")
    
    await close_mongo_connection()


async def revoke_admin_access(email: str):
    """
    Revoke admin privileges from a user.
    
    Usage:
        python -c "import asyncio; from migrations.seed_admin_user import revoke_admin_access; asyncio.run(revoke_admin_access('user@example.com'))"
    """
    await connect_to_mongo()
    await init_db()
    
    user = await UserModel.find_one(UserModel.email == email)
    
    if not user:
        logger.error(f"❌ User not found: {email}")
        await close_mongo_connection()
        return
    
    if not user.is_admin:
        logger.info(f"✓ User is not an admin: {email}")
        await close_mongo_connection()
        return
    
    user.is_admin = False
    await user.save()
    
    logger.info(f"✅ Revoked admin privileges from: {email}")
    await close_mongo_connection()


async def list_admin_users():
    """List all users with admin privileges."""
    await connect_to_mongo()
    await init_db()
    
    admins = await UserModel.find(UserModel.is_admin == True).to_list()
    
    logger.info("\n" + "="*60)
    logger.info(f"👥 ADMIN USERS ({len(admins)} total)")
    logger.info("="*60)
    
    if not admins:
        logger.warning("⚠️  No admin users found in database.")
    else:
        for admin in admins:
            logger.info(f"✓ {admin.email} (username: {admin.username})")
    
    logger.info("="*60)
    
    await close_mongo_connection()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage admin users")
    parser.add_argument(
        "action",
        choices=["seed", "list", "revoke"],
        help="Action to perform"
    )
    parser.add_argument(
        "--email",
        help="Email for revoke action"
    )
    
    args = parser.parse_args()
    
    if args.action == "seed":
        asyncio.run(seed_admin_users())
    elif args.action == "list":
        asyncio.run(list_admin_users())
    elif args.action == "revoke":
        if not args.email:
            logger.error("--email required for revoke action")
            sys.exit(1)
        asyncio.run(revoke_admin_access(args.email))
