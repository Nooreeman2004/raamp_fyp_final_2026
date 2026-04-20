"""
Application Service for handling complaints business logic
"""
from infrastructure.repositories.complaint_repository import ComplaintRepository
from application.services.mailtrap_service import MailtrapService
from application.services.firebase_storage_service import FirebaseStorageService
from infrastructure.repositories.user_repository_impl import UserRepository
from infrastructure.database.models.complaint_model import Comment, StatusUpdate
from application.services.notification_service import NotificationService
from application.services.cloudinary_service import CloudinaryService
from infrastructure.database.models.notification_model import NotificationType
from datetime import datetime
from bson import ObjectId
import asyncio


class ComplaintService:
    def __init__(self):
        self.repo = ComplaintRepository()
        self.mailer = MailtrapService()
        self.user_repo = UserRepository()
        self.storage = FirebaseStorageService()
        self.notifications = NotificationService()
        self.cloudinary = CloudinaryService()

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
                loop.create_task(self._send_ack_email(user_email, user_name, complaint.id, subject, description))
        except Exception:
            pass

        return str(complaint.id)

    async def _send_ack_email(self, email: str, name: str, complaint_id: str, subject: str, description: str):
        try:
            safe_desc = (description or "").strip()
            if len(safe_desc) > 700:
                safe_desc = safe_desc[:700] + "…"
            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">Complaint Received</h2>
                <p>Hi {name},</p>
                <p>We're sorry to hear you're experiencing issues. Your complaint has been received and our team is reviewing it.</p>
                <div style="background: #f5f5f5; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>Complaint ID:</strong> {complaint_id}</p>
                    <p><strong>Subject:</strong> {subject}</p>
                    <p><strong>Details:</strong> {safe_desc}</p>
                    <p><strong>Status:</strong> Pending Review</p>
                </div>
                <p>We aim to respond within <strong>2–3 business days</strong>. Thank you for your patience.</p>
                <p>Best regards,<br>RAAMP Support Team</p>
            </div>
            """
            text = (
                f"Hi {name},\n\n"
                f"We're sorry to hear you're experiencing issues. Your complaint has been received.\n\n"
                f"Complaint ID: {complaint_id}\n"
                f"Subject: {subject}\n"
                f"Details: {safe_desc}\n\n"
                f"We aim to respond within 2–3 business days.\n\n"
                f"— RAAMP Support Team"
            )
            await self.mailer.send_custom_email(email, name, f"RAAMP Support — Complaint Received ({complaint_id})", html, text)
        except Exception:
            return False

    async def get_complaints_for_user(self, user_id: str, limit: int = 50, offset: int = 0):
        complaints = await self.repo.find_by_user_id_paginated(user_id, limit=limit, offset=offset)
        result = []
        for c in complaints:
            signed_attachments: list[str] = []
            for a in (c.attachments or []):
                raw = str(a or "")
                if raw.startswith("cld-auth:"):
                    # format: cld-auth:<resource_type>:<public_id>
                    try:
                        _, res_type, public_id = raw.split(":", 2)
                    except ValueError:
                        res_type, public_id = "raw", raw.replace("cld-auth:", "", 1)
                    url = self.cloudinary.build_authenticated_signed_url(public_id=public_id, resource_type=res_type)
                    if url:
                        signed_attachments.append(url)
                else:
                    signed_attachments.append(raw)

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
                "attachments": signed_attachments,
            })
        return result

    async def admin_list_complaints(self, limit: int = 50, offset: int = 0, status: str | None = None, q: str | None = None):
        complaints = await self.repo.admin_list_paginated(limit=limit, offset=offset, status=status, q=q)
        result = []
        for c in complaints:
            # Admin endpoint: do NOT generate signed URLs for attachments by default.
            # Keep raw references for now; if admin needs access, build a separate audited endpoint.
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
            })
        return result

    async def admin_update_status(
        self,
        complaint_id: str,
        status: str,
        admin_email: str,
        admin_response: str = "",
        comment: str = "",
    ) -> bool:
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint:
            return False

        prev_status = str(getattr(complaint, "status", "") or "").strip().lower()
        complaint.status = status
        complaint.adminId = admin_email
        if admin_response is not None:
            complaint.adminResponse = admin_response
        if status == "resolved":
            complaint.resolvedAt = datetime.utcnow()
        complaint.statusUpdates.append(
            StatusUpdate(
                status=status,
                timestamp=datetime.utcnow(),
                comment=comment or "",
                adminId=admin_email or "",
            )
        )
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()

        # Notify user (email + in-app notification) when support changes status
        try:
            user = await self.user_repo.find_by_id(str(complaint.userId))
            if user and getattr(user, "email", None):
                user_email = str(user.email)
                user_name = str(getattr(user, "first_name", "") or getattr(user, "username", "") or user_email)
                new_status = str(status or "").strip()

                # In-app notification uses email as user_id in notifications collection
                try:
                    title = "Support ticket updated"
                    msg = f"Your complaint “{complaint.subject}” status changed to {new_status}."
                    await self.notifications.create_and_send(
                        user_id=user_email,
                        type=NotificationType.MESSAGE,
                        title=title,
                        message=msg,
                        related_entity_id=str(complaint.id),
                        metadata={
                            "sub_type": "complaint_status",
                            "complaint_id": str(complaint.id),
                            "previous_status": prev_status,
                            "new_status": new_status,
                        },
                        priority=1 if new_status.lower() in {"resolved", "rejected"} else 0,
                    )
                except Exception:
                    # Never block support actions due to notification issues
                    pass

                # Email notification (best-effort, async)
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(
                        self._send_status_update_email(
                            user_email=user_email,
                            user_name=user_name,
                            complaint_id=str(complaint.id),
                            subject=str(complaint.subject or ""),
                            previous_status=prev_status,
                            new_status=new_status,
                            admin_response=str(complaint.adminResponse or ""),
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass
        return True

    async def _send_status_update_email(
        self,
        user_email: str,
        user_name: str,
        complaint_id: str,
        subject: str,
        previous_status: str,
        new_status: str,
        admin_response: str = "",
    ) -> bool:
        try:
            safe_subject = (subject or "").strip()
            safe_prev = (previous_status or "").strip() or "pending"
            safe_new = (new_status or "").strip() or "updated"
            safe_admin = (admin_response or "").strip()
            if len(safe_admin) > 900:
                safe_admin = safe_admin[:900] + "…"

            response_block = ""
            if safe_admin:
                response_block = f"""
                <div style="background:#f5f5f5;padding:12px 14px;border-radius:8px;margin-top:12px;">
                  <p style="margin:0;"><strong>Support message:</strong></p>
                  <p style="margin:8px 0 0 0;white-space:pre-wrap;">{safe_admin}</p>
                </div>
                """

            html = f"""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
              <h2 style="color:#333;">Support Ticket Updated</h2>
              <p>Hi {user_name},</p>
              <p>Your support ticket status has changed.</p>
              <div style="background:#f5f5f5;padding:15px;border-radius:8px;margin:20px 0;">
                <p><strong>Complaint ID:</strong> {complaint_id}</p>
                <p><strong>Subject:</strong> {safe_subject}</p>
                <p><strong>Status:</strong> {safe_prev} → {safe_new}</p>
              </div>
              {response_block}
              <p>If you have more details to add, you can reply in the app under Support.</p>
              <p>— RAAMP Support Team</p>
            </div>
            """

            text = (
                f"Hi {user_name},\n\n"
                f"Your support ticket status has changed.\n\n"
                f"Complaint ID: {complaint_id}\n"
                f"Subject: {safe_subject}\n"
                f"Status: {safe_prev} -> {safe_new}\n\n"
                + (f"Support message:\n{safe_admin}\n\n" if safe_admin else "")
                + "You can view details in the app under Support.\n\n"
                + "— RAAMP Support Team"
            )

            return await self.mailer.send_custom_email(
                user_email,
                user_name,
                f"RAAMP Support — Ticket Updated ({complaint_id})",
                html,
                text,
            )
        except Exception:
            return False

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
        """Upload complaint attachment to Cloudinary (authenticated) and store reference on complaint."""
        complaint = await self.repo.find_by_id(complaint_id)
        if not complaint or complaint.userId != user_id:
            return None

        if not self.cloudinary.is_available:
            # In production we should not store attachments on local disk
            raise RuntimeError("Attachment upload unavailable")

        folder = f"raamp_complaints/{user_id}/{complaint_id}"
        upload_result = await asyncio.to_thread(
            self.cloudinary.upload_file_from_bytes,
            file_content,
            folder,
            file_name,
            False,  # validate_aspect_ratio
            False,  # optimize_for_stories
            True,   # authenticated
        )
        if not upload_result or not upload_result.get("public_id"):
            raise RuntimeError("Attachment upload failed")

        public_id = str(upload_result["public_id"])
        resource_type = str(upload_result.get("resource_type") or "raw")
        # Store as internal reference; signed URLs are generated at read time.
        ref = f"cld-auth:{resource_type}:{public_id}"
        complaint.attachments.append(ref)
        complaint.updatedAt = datetime.utcnow()
        await complaint.save()

        url = self.cloudinary.build_authenticated_signed_url(public_id=public_id, resource_type=resource_type)
        return url
