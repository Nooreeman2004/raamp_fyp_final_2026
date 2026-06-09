#!/usr/bin/env python3
"""
Diagnostic script for auto-reply issues.
Shows failed comment events and connection status.
"""
import asyncio
import sys
import os
from datetime import datetime
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from infrastructure.database.models.auto_reply_models import CommentEventModel, CommentEventStatus
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel
from infrastructure.database.models.facebook_connection_model import FacebookConnectionModel
from infrastructure.database.models.user_model import UserModel
from config import settings


async def diagnose(user_email: str):
    """Diagnose why auto-replies aren't working for a user."""
    client = AsyncIOMotorClient(settings.MONGO_URI)
    db = client["raamp_db"]
    await init_beanie(
        database=db,
        document_models=[
            CommentEventModel,
            InstagramConnectionModel,
            FacebookConnectionModel,
            UserModel,
        ],
    )

    print(f"\n🔍 Diagnosing auto-replies for: {user_email}\n")
    print("=" * 60)

    # Check user exists
    user = await UserModel.find_one(UserModel.email == user_email)
    if not user:
        print(f"❌ User not found: {user_email}")
        return

    print(f"✅ User found: {user.email}")
    print(f"   ID: {user.id}")
    print()

    # Check Instagram connection (use email, not MongoDB ID)
    ig_conn = await InstagramConnectionModel.find_one(InstagramConnectionModel.user_id == user.email)
    if ig_conn:
        print(f"✅ Instagram connected:")
        print(f"   ig_business_id: {ig_conn.ig_business_id}")
        print(f"   username: {ig_conn.username}")
        print(f"   linked_fb_page_id: {ig_conn.linked_fb_page_id}")
        print(f"   token_valid: {ig_conn.token_valid}")
    else:
        print("❌ No Instagram connection found")
    print()

    # Check Facebook connection (use email, not MongoDB ID)
    fb_conn = await FacebookConnectionModel.find_one(FacebookConnectionModel.user_id == user.email)
    if fb_conn:
        print(f"✅ Facebook connected:")
        if fb_conn.fb_pages:
            for page in fb_conn.fb_pages:
                # FBPage is a Pydantic model, access attributes directly
                page_name = getattr(page, 'name', 'Unknown')
                page_id = getattr(page, 'id', 'Unknown')
                print(f"   Page: {page_name} (ID: {page_id})")
    else:
        print("❌ No Facebook connection found")
    print()

    # Import AutoReplyDraftModel to check for actual drafts
    from infrastructure.database.models.auto_reply_models import AutoReplyDraftModel
    await init_beanie(
        database=client["raamp_db"],
        document_models=[
            CommentEventModel,
            InstagramConnectionModel,
            FacebookConnectionModel,
            UserModel,
            AutoReplyDraftModel,
        ],
    )

    # Check for active/recent drafts
    all_drafts = await AutoReplyDraftModel.find(
        AutoReplyDraftModel.user_id == user.email
    ).sort("-created_at").limit(10).to_list()

    if all_drafts:
        print(f"📝 Found {len(all_drafts)} auto-reply drafts:")
        for draft in all_drafts:
            print(f"   {draft.status.upper()}: {draft.suggested_reply[:50]}... (created {draft.created_at})")
        print()
    else:
        print("📝 No auto-reply drafts found")
        print()

    # Check ALL recent events (last 7 days)
    from datetime import timedelta
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    recent_events = await CommentEventModel.find(
        CommentEventModel.created_at >= week_ago
    ).sort("-created_at").limit(20).to_list()

    if recent_events:
        print(f"📬 Found {len(recent_events)} comment events in last 7 days:")
        for ev in recent_events:
            status_emoji = "✅" if ev.status == "processed" else ("⚠️" if ev.status == "failed" else "⏳")
            print(f"\n   {status_emoji} {ev.status.upper()} - {ev.platform}")
            print(f"      Comment: {ev.text[:50]}...")
            print(f"      ID: {ev.comment_id}")
            if ev.status == "failed":
                print(f"      Error: {ev.error}")
            if ev.platform == "instagram":
                print(f"      ig_business_id: {ev.ig_business_id}")
                print(f"      media_id: {ev.media_id}")
            else:
                print(f"      page_id: {ev.page_id}")
            print(f"      Created: {ev.created_at}")
        print()
    else:
        print("📬 No comment events in last 7 days")
        print()

    # Check old failed events separately
    old_failed = await CommentEventModel.find(
        CommentEventModel.status == CommentEventStatus.FAILED,
        CommentEventModel.created_at < week_ago
    ).sort("-created_at").limit(5).to_list()

    if old_failed:
        print(f"🗄️  Found {len(old_failed)} older failed events (>7 days ago) - likely before connection was set up")
        print()

    # Check received events (still pending)
    received_events = await CommentEventModel.find(
        CommentEventModel.status == CommentEventStatus.RECEIVED
    ).sort("-created_at").limit(5).to_list()

    if received_events:
        print(f"⏳ Found {len(received_events)} pending events (waiting for worker):")
        for ev in received_events:
            print(f"   {ev.platform} - {ev.comment_id} - {ev.text[:40]}...")
    else:
        print("✅ No pending events")
    print()

    print("=" * 60)
    print("\n💡 Diagnosis:")
    
    has_connection = (ig_conn and ig_conn.token_valid) or (fb_conn and fb_conn.token_valid)
    has_recent_events = len(recent_events) > 0 if 'recent_events' in locals() else False
    has_drafts = len(all_drafts) > 0 if 'all_drafts' in locals() else False
    
    if not has_connection:
        print("   ❌ No active social media connection")
        print("   → Connect Instagram or Facebook in Settings")
    elif has_connection and has_recent_events and not has_drafts:
        print("   ⚠️  Connection exists, events received, but NO drafts created")
        print("   → Check if auto-replies are enabled in Settings")
        print("   → Check worker logs for processing errors")
        recent_failed = [e for e in recent_events if e.status == "failed"]
        if recent_failed:
            print(f"   → {len(recent_failed)} events failed - check error messages above")
    elif has_connection and not has_recent_events:
        print("   ⏳ Connection exists, but no recent comment events")
        print("   → Comment on your Instagram/Facebook post to test")
        print("   → Verify Meta webhook is configured correctly")
    elif has_connection and has_drafts:
        print("   ✅ System is working! Drafts are being created")
        print("   → Check /dashboard/auto-replies to review them")
    else:
        print("   ℹ️  Run this script after commenting on a post to see results")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_auto_replies.py <user_email>")
        sys.exit(1)

    email = sys.argv[1].strip().lower()
    asyncio.run(diagnose(email))
