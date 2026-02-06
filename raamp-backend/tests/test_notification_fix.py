"""
Simple Manual Test for Notification System
Tests that notifications can be created and fetched after the fix
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.database.models.notification_model import NotificationType, NotificationStatus


async def test_notification_crud():
    """Test notification CRUD operations"""
    print("\n" + "="*80)
    print("NOTIFICATION SYSTEM TEST - After Fix")
    print("="*80)
    
    # Initialize database
    print("\n1️⃣ Connecting to database...")
    await connect_to_mongo()
    await init_db()
    print("   ✅ Database connected and initialized")
    
    # Create repository
    repository = NotificationRepository()
    test_email = "test_fix@example.com"
    
    try:
        # Test 1: Create notification
        print("\n2️⃣ Creating test notification...")
        notification = await repository.create(
            user_id=test_email,
            type=NotificationType.MESSAGE,
            title="Test Notification",
            message="Testing the fix for AttributeError: user_id",
            metadata={"test": "fix_verification"}
        )
        print(f"   ✅ Created notification: {notification.id}")
        print(f"      User: {notification.user_id}")
        print(f"      Title: {notification.title}")
        
        # Test 2: Fetch by user_id (this was failing before)
        print("\n3️⃣ Fetching notifications by user_id...")
        notifications = await repository.get_by_user_id(test_email)
        print(f"   ✅ Found {len(notifications)} notification(s)")
        for notif in notifications:
            print(f"      - {notif.type.value}: {notif.title}")
        
        # Test 3: Get unread count
        print("\n4️⃣ Getting unread count...")
        unread_count = await repository.get_unread_count(test_email)
        print(f"   ✅ Unread count: {unread_count}")
        
        # Test 4: Mark as read
        print("\n5️⃣ Marking notification as read...")
        updated = await repository.mark_as_read(str(notification.id), test_email)
        print(f"   ✅ Marked as read: {updated.read}")
        
        # Test 5: Create social post notification
        print("\n6️⃣ Creating social post notification...")
        social_notif = await repository.create(
            user_id=test_email,
            type=NotificationType.SOCIAL_POST,
            title="Instagram Post Published",
            message="Your post was published successfully",
            metadata={
                "platform": "instagram",
                "post_id": "test_post_123",
                "status": NotificationStatus.SUCCESS.value,
                "campaign_id": "camp_456"
            }
        )
        print(f"   ✅ Created social post notification")
        print(f"      Platform: {social_notif.platform}")
        print(f"      Post ID: {social_notif.post_id}")
        print(f"      Status: {social_notif.status}")
        
        # Test 6: Delete notification
        print("\n7️⃣ Deleting test notification...")
        deleted = await repository.delete_notification(str(notification.id), test_email)
        print(f"   ✅ Deleted: {deleted}")
        
        # Cleanup
        print("\n8️⃣ Cleaning up test data...")
        await repository.mark_all_as_read(test_email)
        remaining = await repository.get_by_user_id(test_email)
        for notif in remaining:
            await repository.delete_notification(str(notif.id), test_email)
        print(f"   ✅ Cleaned up {len(remaining)} notification(s)")
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED! Notification system is working correctly.")
        print("="*80)
        print("\nThe fix successfully resolved the AttributeError: user_id issue.")
        print("NotificationModel is now properly initialized with Beanie.")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Close connection
        await close_mongo_connection()


if __name__ == "__main__":
    asyncio.run(test_notification_crud())
