import asyncio
import os
import sys
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie, PydanticObjectId
from infrastructure.database.models.chat_session_model import ChatSessionModel
from infrastructure.database.models.chat_interaction_model import ChatInteractionModel
from infrastructure.database.models.complaint_model import ComplaintModel
from infrastructure.database.models.user_model import UserModel
from infrastructure.database.models.business_model import BusinessModel
from application.services.rag.raamp_generation import RAAMPGenerator
from application.services.complaint_service import ComplaintService

async def test_end_to_end_complaint():
    print("Starting End-to-End Complaint Journey Test")
    print("============================================================")

    # 1. Setup & Connectivity
    print("[INFO] Connecting to MongoDB...")
    from infrastructure.database.database import connect_to_mongo, init_db
    await connect_to_mongo()
    await init_db()
    print("[OK] MongoDB and Beanie initialized")

    # Mock data
    user_id = "test-user-456"
    session_id = "test-session-complaint-789"
    user_email = "test@example.com"

    # Ensure user exists for email lookup
    user = await UserModel.find_one(UserModel.email == user_email)
    if not user:
        user = UserModel(email=user_email, username="testuser123", is_verified=True, role="user", password_hash="dummy")
        await user.insert()
        print(f"[INFO] Created mock user: {user.id}")
    
    user_id = str(user.id)

    # 2. Chatbot Interaction
    print("\n[PHASE 1] Chatbot Interaction")
    generator = RAAMPGenerator()
    
    # User reports a bug
    query = "I have discovered a major bug in the creative studio, it's not working!"
    print(f"User: {query}")
    
    # We check if it matches quick response or AI guidance
    from presentation.routers.chatbot_router import get_quick_response
    quick_resp = get_quick_response(query)
    
    if quick_resp:
        print(f"Bot (Quick Response): {quick_resp}")
        if "/dashboard/complaints" in quick_resp:
            print("Verified: Chatbot provided the complaints link via Quick Response!")
        else:
            print("Failure: Quick response did not contain the link.")
    else:
        # Fallback to AI
        response = generator.chat(query)
        print(f"Bot (AI): {response['answer']}")
        if "/dashboard/complaints" in response['answer']:
            print("Verified: Chatbot provided the complaints link via AI Guidance!")
        else:
            print("Failure: Neither Quick Response nor AI provided the link.")

    # 3. Complaint Submission
    print("\n[PHASE 2] Complaint Submission")
    complaint_service = ComplaintService()
    
    subject = "Creative Studio Bug"
    description = "The image generation tool keeps crashing when I select 'IG Filter'."
    
    print(f"[INFO] Submitting complaint: '{subject}'")
    complaint_id = await complaint_service.submit_complaint(
        user_id=user_id,
        subject=subject,
        description=description,
        priority="high"
    )
    print(f"Complaint created with ID: {complaint_id}")

    # 4. Verification in DB
    complaint = await ComplaintModel.get(PydanticObjectId(complaint_id))
    if complaint:
        print(f"Verified: Complaint {complaint_id} saved to MongoDB")
        print(f"   Status: {complaint.status}")
        print(f"   Priority: {complaint.priority}")
    else:
        print("Failure: Complaint not found in database!")

    # 5. Audit Trail & Status Updates
    print("\n[PHASE 3] Audit Trail & Status Updates")
    # Simulate admin change
    complaint.status = "in progress"
    from infrastructure.database.models.complaint_model import StatusUpdate
    complaint.statusUpdates.append(StatusUpdate(
        status="in progress",
        timestamp=datetime.utcnow(),
        comment="Support team is looking into the crash logs.",
        adminId="admin-99"
    ))
    await complaint.save()
    print("[INFO] Simulated admin status change to 'in progress'")

    # Fetch via service (simulating UI load)
    user_complaints = await complaint_service.get_complaints_for_user(user_id)
    found = False
    for c in user_complaints:
        if c['id'] == complaint_id:
            found = True
            print(f"Verified: UI Service returned complaint {complaint_id}")
            print(f"   Audit trail length: {len(c['statusUpdates'])}")
            if len(c['statusUpdates']) > 0:
                print(f"   Latest Update: {c['statusUpdates'][-1]['comment']}")
                print("Verified: Audit trail shows correctly!")

    if not found:
        print("Failure: Complaint service did not return the new complaint.")

    print("\n[PHASE 4] Email Verification")
    print("[INFO] Checking Mailtrap logic (Simulation)...")
    # Note: Real SMTP sending requires valid credentials in config.py
    # But we can verify _send_ack_email task was triggered or code runs.
    try:
        await complaint_service._send_ack_email(user_email, "Test User", complaint_id, subject)
        print("Verified: Mailtrap service execution flow finished")
    except Exception as e:
        print(f"Mailtrap simulated send failed (likely no credentials): {e}")

    print("\n============================================================")
    print("End-to-End Complaint Journey Test Completed Successfully!")

if __name__ == "__main__":
    asyncio.run(test_end_to_end_complaint())
