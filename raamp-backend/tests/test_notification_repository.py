"""
Unit Tests for Notification Repository
Tests CRUD operations including create, fetch by user_id, mark as read, and delete
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from datetime import datetime
from infrastructure.database.models.notification_model import NotificationModel, NotificationType, NotificationStatus
from infrastructure.repositories.notification_repository import NotificationRepository
from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_database():
    """Initialize database connection before all tests"""
    await connect_to_mongo()
    await init_db()
    yield
    await close_mongo_connection()


@pytest.fixture
def notification_repository():
    """Create a notification repository instance"""
    return NotificationRepository()


@pytest.fixture
def test_user_email():
    """Test user email"""
    return "test_notifications@example.com"


@pytest.fixture
async def cleanup_notifications(test_user_email):
    """Clean up test notifications after each test"""
    yield
    # Cleanup after test
    await NotificationModel.find(
        NotificationModel.user_id == test_user_email
    ).delete()


class TestNotificationRepository:
    """Test suite for NotificationRepository"""
    
    @pytest.mark.asyncio
    async def test_create_notification(
        self, 
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test creating a basic notification"""
        print("\n" + "="*80)
        print("TEST: Create Notification")
        print("="*80)
        
        # Create notification
        notification = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.MESSAGE,
            title="Test Notification",
            message="This is a test notification message",
            metadata={"source": "unit_test"}
        )
        
        print(f"✅ Created notification:")
        print(f"   ID: {notification.id}")
        print(f"   User: {notification.user_id}")
        print(f"   Type: {notification.type}")
        print(f"   Title: {notification.title}")
        print(f"   Read: {notification.read}")
        
        # Assertions
        assert notification is not None
        assert notification.id is not None
        assert notification.user_id == test_user_email
        assert notification.type == NotificationType.MESSAGE
        assert notification.title == "Test Notification"
        assert notification.message == "This is a test notification message"
        assert notification.read is False
        assert notification.metadata["source"] == "unit_test"
        
        print("\n✅ TEST PASSED: Notification created successfully")
    
    @pytest.mark.asyncio
    async def test_fetch_by_user_id(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test fetching notifications by user_id"""
        print("\n" + "="*80)
        print("TEST: Fetch Notifications by user_id")
        print("="*80)
        
        # Create multiple notifications
        notification1 = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.ALERT,
            title="Alert 1",
            message="First alert"
        )
        
        notification2 = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.REMINDER,
            title="Reminder 1",
            message="First reminder"
        )
        
        notification3 = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.SYSTEM,
            title="System 1",
            message="First system message"
        )
        
        print(f"✅ Created 3 test notifications")
        
        # Fetch notifications
        notifications = await notification_repository.get_by_user_id(test_user_email)
        
        print(f"\n📥 Fetched {len(notifications)} notifications:")
        for idx, notif in enumerate(notifications, 1):
            print(f"   {idx}. {notif.type.value}: {notif.title}")
        
        # Assertions
        assert len(notifications) == 3
        assert all(n.user_id == test_user_email for n in notifications)
        
        # Check ordering (should be newest first)
        assert notifications[0].created_at >= notifications[1].created_at
        assert notifications[1].created_at >= notifications[2].created_at
        
        print("\n✅ TEST PASSED: Notifications fetched correctly by user_id")
    
    @pytest.mark.asyncio
    async def test_get_unread_count(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test getting unread notification count"""
        print("\n" + "="*80)
        print("TEST: Get Unread Count")
        print("="*80)
        
        # Create 5 notifications (all unread)
        for i in range(5):
            await notification_repository.create(
                user_id=test_user_email,
                type=NotificationType.MESSAGE,
                title=f"Message {i+1}",
                message=f"Test message {i+1}"
            )
        
        print(f"✅ Created 5 unread notifications")
        
        # Get unread count
        unread_count = await notification_repository.get_unread_count(test_user_email)
        
        print(f"📊 Unread count: {unread_count}")
        
        # Assertions
        assert unread_count == 5
        
        # Mark 2 as read
        notifications = await notification_repository.get_by_user_id(test_user_email, limit=2)
        for notif in notifications:
            await notification_repository.mark_as_read(str(notif.id), test_user_email)
        
        print(f"✅ Marked 2 notifications as read")
        
        # Get updated unread count
        unread_count_after = await notification_repository.get_unread_count(test_user_email)
        
        print(f"📊 Unread count after marking 2 as read: {unread_count_after}")
        
        # Assertions
        assert unread_count_after == 3
        
        print("\n✅ TEST PASSED: Unread count works correctly")
    
    @pytest.mark.asyncio
    async def test_mark_as_read(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test marking a notification as read"""
        print("\n" + "="*80)
        print("TEST: Mark Notification as Read")
        print("="*80)
        
        # Create notification
        notification = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.ALERT,
            title="Test Alert",
            message="This should be marked as read"
        )
        
        print(f"✅ Created notification (read={notification.read})")
        
        # Mark as read
        updated = await notification_repository.mark_as_read(
            str(notification.id),
            test_user_email
        )
        
        print(f"✅ Marked notification as read (read={updated.read})")
        
        # Assertions
        assert updated is not None
        assert updated.read is True
        
        # Verify in database
        notifications = await notification_repository.get_by_user_id(test_user_email)
        assert notifications[0].read is True
        
        print("\n✅ TEST PASSED: Notification marked as read successfully")
    
    @pytest.mark.asyncio
    async def test_mark_all_as_read(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test marking all notifications as read"""
        print("\n" + "="*80)
        print("TEST: Mark All Notifications as Read")
        print("="*80)
        
        # Create 10 unread notifications
        for i in range(10):
            await notification_repository.create(
                user_id=test_user_email,
                type=NotificationType.MESSAGE,
                title=f"Message {i+1}",
                message=f"Test message {i+1}"
            )
        
        print(f"✅ Created 10 unread notifications")
        
        # Get initial unread count
        unread_before = await notification_repository.get_unread_count(test_user_email)
        print(f"📊 Unread before: {unread_before}")
        
        # Mark all as read
        modified_count = await notification_repository.mark_all_as_read(test_user_email)
        
        print(f"✅ Marked all as read (modified: {modified_count})")
        
        # Get updated unread count
        unread_after = await notification_repository.get_unread_count(test_user_email)
        print(f"📊 Unread after: {unread_after}")
        
        # Assertions
        assert unread_before == 10
        assert modified_count == 10
        assert unread_after == 0
        
        # Verify all are marked as read
        all_notifications = await notification_repository.get_by_user_id(test_user_email)
        assert all(n.read is True for n in all_notifications)
        
        print("\n✅ TEST PASSED: All notifications marked as read")
    
    @pytest.mark.asyncio
    async def test_create_social_post_notification(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test creating a social post notification with metadata"""
        print("\n" + "="*80)
        print("TEST: Create Social Post Notification")
        print("="*80)
        
        # Create social post notification
        notification = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.SOCIAL_POST,
            title="Instagram Post Published",
            message="Your scheduled post has been successfully published to Instagram",
            metadata={
                "platform": "instagram",
                "post_id": "post_12345",
                "status": NotificationStatus.SUCCESS.value,
                "campaign_id": "campaign_abc"
            }
        )
        
        print(f"✅ Created social post notification:")
        print(f"   Platform: {notification.platform}")
        print(f"   Post ID: {notification.post_id}")
        print(f"   Status: {notification.status}")
        print(f"   Campaign ID: {notification.campaign_id}")
        
        # Assertions
        assert notification.type == NotificationType.SOCIAL_POST
        assert notification.platform == "instagram"
        assert notification.post_id == "post_12345"
        assert notification.status == NotificationStatus.SUCCESS
        assert notification.campaign_id == "campaign_abc"
        
        print("\n✅ TEST PASSED: Social post notification created with metadata")
    
    @pytest.mark.asyncio
    async def test_delete_notification(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test deleting a notification"""
        print("\n" + "="*80)
        print("TEST: Delete Notification")
        print("="*80)
        
        # Create notification
        notification = await notification_repository.create(
            user_id=test_user_email,
            type=NotificationType.SYSTEM,
            title="To Be Deleted",
            message="This notification will be deleted"
        )
        
        notification_id = str(notification.id)
        print(f"✅ Created notification (ID: {notification_id})")
        
        # Delete notification
        deleted = await notification_repository.delete_notification(
            notification_id,
            test_user_email
        )
        
        print(f"✅ Deleted notification: {deleted}")
        
        # Assertions
        assert deleted is True
        
        # Verify it's gone
        notifications = await notification_repository.get_by_user_id(test_user_email)
        assert len(notifications) == 0
        
        print("\n✅ TEST PASSED: Notification deleted successfully")
    
    @pytest.mark.asyncio
    async def test_pagination(
        self,
        notification_repository: NotificationRepository,
        test_user_email: str,
        cleanup_notifications
    ):
        """Test pagination of notifications"""
        print("\n" + "="*80)
        print("TEST: Notification Pagination")
        print("="*80)
        
        # Create 25 notifications
        for i in range(25):
            await notification_repository.create(
                user_id=test_user_email,
                type=NotificationType.MESSAGE,
                title=f"Message {i+1}",
                message=f"Test message {i+1}"
            )
        
        print(f"✅ Created 25 notifications")
        
        # Test pagination
        page1 = await notification_repository.get_by_user_id(
            test_user_email, 
            limit=10, 
            offset=0
        )
        
        page2 = await notification_repository.get_by_user_id(
            test_user_email,
            limit=10,
            offset=10
        )
        
        page3 = await notification_repository.get_by_user_id(
            test_user_email,
            limit=10,
            offset=20
        )
        
        print(f"📄 Page 1: {len(page1)} notifications")
        print(f"📄 Page 2: {len(page2)} notifications")
        print(f"📄 Page 3: {len(page3)} notifications")
        
        # Assertions
        assert len(page1) == 10
        assert len(page2) == 10
        assert len(page3) == 5  # Only 5 remaining
        
        # Ensure no duplicates across pages
        all_ids = [str(n.id) for n in page1 + page2 + page3]
        assert len(all_ids) == len(set(all_ids))  # All unique
        
        print("\n✅ TEST PASSED: Pagination works correctly")


def run_tests():
    """Run all tests with pytest"""
    print("\n")
    print("╔" + "═"*78 + "╗")
    print("║" + " "*20 + "NOTIFICATION REPOSITORY UNIT TESTS" + " "*24 + "║")
    print("╚" + "═"*78 + "╝")
    
    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",  # Verbose
        "-s",  # Show print statements
        "--tb=short",  # Short traceback format
        "--asyncio-mode=auto"  # Auto detect async tests
    ])
    
    return exit_code


if __name__ == "__main__":
    exit(run_tests())
