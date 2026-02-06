"""
Application Service for handling complaints business logic
"""
from infrastructure.repositories.complaint_repository import ComplaintRepository
from application.services.mailtrap_service import MailtrapService
from application.services.firebase_storage_service import FirebaseStorageService
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.database.models.complaint_model import Comment
from datetime import datetime
from bson import ObjectId
import asyncio


class ComplaintService:
    def __init__(self):
        self.repo = ComplaintRepository()
        self.mailer = MailtrapService()
        self.user_repo = UserRepository()
        self.storage = FirebaseStorageService()

    async def submit_complaint(self, user_id: str, subject: str, description: str, priority: str = "medium") -> str:
        """Create a complaint and trigger async acknowledgement email.

        Returns:
            complaint id (string)
        """
        complaint = await self.repo.create(user_id=user_id, subject=subject, description=description, priority=priority)

        # Fire-and-forget acknowledgement email to user's registered email
        try:
            user = await self.user_repo.find_by_id(user_id)
            if user:
                user_email = user.email
                user_name = (user.first_name or user.username or user.email)
            else:
                user_email = None
                user_name = ""

            if user_email:
                loop = asyncio.get_event_loop()
                loop.create_task(self._send_ack_email(user_email, user_name, complaint.id, subject))
        except Exception:
            pass

        return str(complaint.id)

    async def _send_ack_email(self, email: str, name: str, complaint_id: str, subject: str):
        try:
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Complaint Received</h2>
                <p>Hi {name},</p>
                <p>We're sorry to hear you're experiencing issues. Your complaint has been received and our team is reviewing it.</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Complaint ID:</strong> {complaint_id}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <p><strong>Status:</strong> Pending Review</p>
                </div>
                <p>We'll get back to you as soon as possible. Thank you for your patience.</p>
                <p>Best regards,<br>RAAMP Support Team</p>
            </div>
            """
            text = f"Hi {name},\n\nYour complaint {complaint_id} has been received. Subject: {subject}\n\nWe will get back to you shortly."
            await self.mailer.send_custom_email(email, name, f"Complaint Received: {complaint_id}", html, text)
        except Exception:
            return False

    async def get_complaints_for_user(self, user_id: str):
        complaints = await self.repo.find_by_user_id(user_id)
        result = []
        for c in complaints:
            result.append({
                "id": str(c.id),
                "userId": c.userId,
                "subject": c.subject,
                "description": c.description,
                "status": c.status,
                "priority": c.priority,
                "adminResponse": c.adminResponse,
                "adminId": c.adminId,
                "resolvedAt": c.resolvedAt.isoformat() if c.resolvedAt else None,
                "createdAt": c.createdAt.isoformat(),
                "updatedAt": c.updatedAt.isoformat(),
                "statusUpdates": [
                    {
                        "status": s.status,
                        "timestamp": s.timestamp.isoformat(),
                        "comment": s.comment,
                        "adminId": s.adminId,
                    }
                    for s in c.statusUpdates
                ],
                "comments": [
                    {
                        "text": cm.text,
                        "author": cm.author,
                        "timestamp": cm.timestamp.isoformat(),
                    "isAdmin": cm.isAdmin,
                }
                    for cm in (c.comments or [])
                ],
                "rating": c.rating,
                "attachments": c.attachments or [],
            })
        return result

    async def update_complaint(self, complaint_id: str, user_id: str, subject: str, description: str, priority: str) -> bool:
        """Update a pending complaint (only owner can update)"""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id or complaint.status != "pending":
            return False

        complaint.subject = subject
        complaint.description = description
        complaint.priority = priority
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()
        return True

    async def delete_complaint(self, complaint_id: str, user_id: str) -> bool:
        """Delete/cancel a pending complaint (only owner can delete)"""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id or complaint.status != "pending":
            return False

        await complaint.delete()
        return True

    async def add_comment(self, complaint_id: str, user_id: str, text: str) -> bool:
        """Add a comment to a complaint"""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id:
            return False

        # Get user name
        user = await self.user_repo.find_by_id(user_id)
        author = user.first_name or user.username or "User" if user else "User"

        comment = Comment(
            text=text,
            author=author,
            timestamp=datetime.utcnow(),
            isAdmin=False
        )
        complaint.comments.append(comment)
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()
        return True

    async def submit_rating(self, complaint_id: str, user_id: str, rating: int) -> bool:
        """Rate a resolved complaint"""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id or complaint.status != "resolved":
            return False

        complaint.rating = rating
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()
        return True

    async def upload_attachment(self, complaint_id: str, user_id: str, file_content: bytes, file_name: str) -> str:
        """Upload attachment to a complaint (Firebase disabled, using local storage)"""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id:
            return None

        # Firebase Storage Upload (DISABLED - Using local storage only)
        # url = await self.storage.upload_complaint_attachment(
        #     file_content=file_content,
        #     file_name=file_name,
        #     user_id=user_id,
        #     complaint_id=complaint_id
        # )
        
        # Use local storage fallback
        import uuid
        from pathlib import Path
        from config import settings
        
        file_extension = file_name.split('.')[-1].lower()
        unique_filename = f"complaint_attachments/{user_id}/{complaint_id}/{uuid.uuid4()}.{file_extension}"
        
        local_dir = Path("uploaded_files") / "complaint_attachments" / user_id / complaint_id
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / f"{uuid.uuid4()}.{file_extension}"
        
        with open(local_path, 'wb') as f:
            f.write(file_content)
        
        url = f"{settings.BACKEND_URL}/api/static/complaint_attachments/{user_id}/{complaint_id}/{local_path.name}"

        # Add URL to complaint
        complaint.attachments.append(url)
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()

        return url
