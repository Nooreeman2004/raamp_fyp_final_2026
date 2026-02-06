"""
Migration Script: Consolidate Google Place Data into BusinessModel
==================================================================

This script migrates data from:
1. google_business_locations collection -> businesses collection
2. Removes redundant Google fields from users collection (handled via schema update)

Run this script BEFORE updating the application code.
Ensure you have a database backup before running.

Usage:
    cd raamp-backend
    python -m migrations.migrate_google_location_to_business
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

# Load .env file
load_dotenv()

# MongoDB connection - get from environment variable
DATABASE_URL = os.getenv("MONGODB_URL", os.getenv("MONGO_URI", "mongodb://localhost:27017/raamp_db"))
# Extract database name from URI or use default
DATABASE_NAME = DATABASE_URL.rsplit("/", 1)[-1].split("?")[0] if "/" in DATABASE_URL else "raamp_db"

print(f"Using MongoDB URI: {DATABASE_URL[:50]}...")  # Print partial for security
print(f"Database name: {DATABASE_NAME}")


async def migrate_google_locations_to_businesses():
    """
    Migrate all data from google_business_locations to businesses collection.
    
    Strategy:
    - For each google_business_locations document, find/create corresponding business
    - Copy location data (prioritizing google_business_locations as source of truth)
    - Track migration statistics
    """
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    
    google_locations = db["google_business_locations"]
    businesses = db["businesses"]
    users = db["users"]
    
    stats = {
        "total_locations": 0,
        "migrated": 0,
        "created_new_business": 0,
        "updated_existing_business": 0,
        "skipped": 0,
        "errors": []
    }
    
    print("=" * 60)
    print("Starting Google Location -> Business Migration")
    print("=" * 60)
    
    # Step 1: Count documents
    total = await google_locations.count_documents({})
    stats["total_locations"] = total
    print(f"\nFound {total} documents in google_business_locations collection")
    
    if total == 0:
        print("No documents to migrate. Exiting.")
        client.close()
        return stats
    
    # Step 2: Iterate and migrate
    cursor = google_locations.find({})
    
    async for location_doc in cursor:
        user_id = location_doc.get("user_id")
        
        if not user_id:
            stats["skipped"] += 1
            stats["errors"].append(f"Skipped document {location_doc.get('_id')}: no user_id")
            continue
        
        try:
            # Find existing business for this user
            existing_business = await businesses.find_one({"user_id": user_id})
            
            # Prepare location data from google_business_locations
            location_data = {
                "google_place_id": location_doc.get("place_id"),
                "business_name": location_doc.get("business_name"),
                "business_address": location_doc.get("address"),
                "latitude": location_doc.get("latitude"),
                "longitude": location_doc.get("longitude"),
                "updated_at": datetime.utcnow()
            }
            
            # Remove None values to avoid overwriting existing data with nulls
            location_data = {k: v for k, v in location_data.items() if v is not None}
            
            if existing_business:
                # Update existing business - prioritize google_business_locations data
                await businesses.update_one(
                    {"_id": existing_business["_id"]},
                    {"$set": location_data}
                )
                stats["updated_existing_business"] += 1
                print(f"  ✓ Updated business for user: {user_id}")
            else:
                # Create new business document
                new_business = {
                    "user_id": user_id,
                    "created_at": datetime.utcnow(),
                    **location_data
                }
                await businesses.insert_one(new_business)
                stats["created_new_business"] += 1
                print(f"  ✓ Created new business for user: {user_id}")
            
            stats["migrated"] += 1
            
        except Exception as e:
            stats["errors"].append(f"Error migrating user {user_id}: {str(e)}")
            print(f"  ✗ Error for user {user_id}: {e}")
    
    print("\n" + "=" * 60)
    print("Migration Summary")
    print("=" * 60)
    print(f"Total locations found:      {stats['total_locations']}")
    print(f"Successfully migrated:      {stats['migrated']}")
    print(f"  - New businesses created: {stats['created_new_business']}")
    print(f"  - Existing updated:       {stats['updated_existing_business']}")
    print(f"Skipped:                    {stats['skipped']}")
    print(f"Errors:                     {len(stats['errors'])}")
    
    if stats["errors"]:
        print("\nErrors encountered:")
        for err in stats["errors"]:
            print(f"  - {err}")
    
    client.close()
    return stats


async def cleanup_google_locations_collection(dry_run: bool = True):
    """
    Drop the google_business_locations collection after migration.
    
    Args:
        dry_run: If True, only shows what would be deleted without actually deleting
    """
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    
    google_locations = db["google_business_locations"]
    
    count = await google_locations.count_documents({})
    
    if dry_run:
        print(f"\n[DRY RUN] Would drop google_business_locations collection ({count} documents)")
    else:
        print(f"\nDropping google_business_locations collection ({count} documents)...")
        await google_locations.drop()
        print("✓ Collection dropped successfully")
    
    client.close()


async def cleanup_user_google_fields(dry_run: bool = True):
    """
    Remove redundant Google fields from users collection.
    
    Args:
        dry_run: If True, only shows what would be updated without actually updating
    """
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    
    users = db["users"]
    
    # Find users with any Google fields set
    query = {
        "$or": [
            {"google_place_id": {"$exists": True}},
            {"google_place_name": {"$exists": True}},
            {"google_place_address": {"$exists": True}},
            {"google_lat": {"$exists": True}},
            {"google_lng": {"$exists": True}}
        ]
    }
    
    count = await users.count_documents(query)
    
    if dry_run:
        print(f"\n[DRY RUN] Would remove Google fields from {count} user documents")
    else:
        print(f"\nRemoving Google fields from {count} user documents...")
        result = await users.update_many(
            {},
            {
                "$unset": {
                    "google_place_id": "",
                    "google_place_name": "",
                    "google_place_address": "",
                    "google_lat": "",
                    "google_lng": ""
                }
            }
        )
        print(f"✓ Modified {result.modified_count} documents")
    
    client.close()


async def verify_migration():
    """Verify the migration was successful by comparing data."""
    client = AsyncIOMotorClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    
    businesses = db["businesses"]
    
    print("\n" + "=" * 60)
    print("Verification")
    print("=" * 60)
    
    # Check businesses with location data
    with_location = await businesses.count_documents({
        "latitude": {"$exists": True, "$ne": None},
        "longitude": {"$exists": True, "$ne": None}
    })
    
    total_businesses = await businesses.count_documents({})
    
    print(f"Total businesses:              {total_businesses}")
    print(f"Businesses with location data: {with_location}")
    
    # Sample a few records
    print("\nSample business records with location:")
    cursor = businesses.find({
        "latitude": {"$exists": True, "$ne": None}
    }).limit(3)
    
    async for doc in cursor:
        print(f"  - User: {doc.get('user_id')}")
        print(f"    Name: {doc.get('business_name')}")
        print(f"    Address: {doc.get('business_address')}")
        print(f"    Coords: ({doc.get('latitude')}, {doc.get('longitude')})")
        print(f"    Place ID: {doc.get('google_place_id')}")
        print()
    
    client.close()


async def main():
    """Main migration entry point."""
    print("\n" + "=" * 60)
    print("Google Location Data Migration Tool")
    print("=" * 60)
    print("\nThis script will:")
    print("1. Migrate data from google_business_locations -> businesses")
    print("2. Optionally clean up the old collection and user fields")
    print("\n⚠️  Make sure you have a database backup before proceeding!")
    
    # Step 1: Run migration
    print("\n" + "-" * 60)
    print("STEP 1: Migrating location data to businesses collection")
    print("-" * 60)
    stats = await migrate_google_locations_to_businesses()
    
    # Step 2: Verify migration
    await verify_migration()
    
    # Step 3: Cleanup (dry run first)
    print("\n" + "-" * 60)
    print("STEP 2: Cleanup Preview (DRY RUN)")
    print("-" * 60)
    await cleanup_google_locations_collection(dry_run=True)
    await cleanup_user_google_fields(dry_run=True)
    
    # Prompt for actual cleanup
    print("\n" + "-" * 60)
    print("STEP 3: Cleanup Execution")
    print("-" * 60)
    print("\nTo execute cleanup, run this script with --cleanup flag")
    print("Or call cleanup functions directly with dry_run=False")
    
    return stats


async def run_cleanup():
    """Execute the cleanup phase (drop collection, remove user fields)."""
    print("\n⚠️  Executing cleanup - this is irreversible!")
    await cleanup_google_locations_collection(dry_run=False)
    await cleanup_user_google_fields(dry_run=False)
    print("\n✓ Cleanup completed successfully")


if __name__ == "__main__":
    import sys
    
    if "--cleanup" in sys.argv:
        asyncio.run(run_cleanup())
    else:
        asyncio.run(main())
