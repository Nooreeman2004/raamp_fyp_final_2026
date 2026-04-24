from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from presentation.schemas.complaint_schemas import (
    ComplaintSubmitRequest,
    ComplaintSubmitResponse,
    ComplaintResponseItem,
    ComplaintUpdateRequest,
    ComplaintCommentRequest,
    ComplaintRatingRequest,
)
from application.services.complaint_service import ComplaintService
from application.constants import FileLimits
from presentation.routers.auth_router import get_current_user_id, get_current_user_email, require_admin_role
from infrastructure.database.models.user_model import UserModel
from fastapi.responses import JSONResponse
from typing import Optional
import logging
from infrastructure.repositories.user_repository_impl import UserRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/complaints", tags=["complaints"])
service = ComplaintService()
user_repo = UserRepository()


# Admin endpoints use require_admin_role dependency


@router.post("/submit", response_model=ComplaintSubmitResponse, status_code=status.HTTP_201_CREATED)
async def submit_complaint(payload: ComplaintSubmitRequest, user_id: str = Depends(get_current_user_id)):
    """Submit a new complaint"""
    try:
        complaint_id = await service.submit_complaint(
            user_id=user_id,
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority
        )
        return ComplaintSubmitResponse(id=complaint_id)
    except Exception as e:
        logger.exception("Complaint submit failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit complaint")


@router.get("/user", response_model=list[ComplaintResponseItem])
async def get_user_complaints(
    user_id: str = Depends(get_current_user_id),
    limit: int = 50,
    offset: int = 0,
):
    """Get all complaints for the authenticated user"""
    try:
        complaints = await service.get_complaints_for_user(user_id, limit=limit, offset=offset)
        return JSONResponse(status_code=status.HTTP_200_OK, content=complaints)
    except Exception as e:
        logger.exception("Get user complaints failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load complaints")


@router.put("/{complaint_id}")
async def update_complaint(complaint_id: str, payload: ComplaintUpdateRequest, user_id: str = Depends(get_current_user_id)):
    """Update a pending complaint (only owner can update)"""
    try:
        updated = await service.update_complaint(
            complaint_id=complaint_id,
            user_id=user_id,
            subject=payload.subject,
            description=payload.description,
            priority=payload.priority
        )
        if not updated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found or cannot be edited")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Update complaint failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update complaint")


@router.delete("/{complaint_id}")
async def delete_complaint(complaint_id: str, user_id: str = Depends(get_current_user_id)):
    """Cancel/delete a pending complaint (only owner can delete)"""
    try:
        deleted = await service.delete_complaint(complaint_id=complaint_id, user_id=user_id)
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found or cannot be deleted")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Delete complaint failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete complaint")


@router.post("/{complaint_id}/comments")
async def add_comment(complaint_id: str, payload: ComplaintCommentRequest, user_id: str = Depends(get_current_user_id)):
    """Add a comment to a complaint"""
    try:
        added = await service.add_comment(complaint_id=complaint_id, user_id=user_id, text=payload.text)
        if not added:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Add comment failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add comment")


@router.post("/{complaint_id}/rating")
async def submit_rating(complaint_id: str, payload: ComplaintRatingRequest, user_id: str = Depends(get_current_user_id)):
    """Rate a resolved complaint"""
    try:
        rated = await service.submit_rating(complaint_id=complaint_id, user_id=user_id, rating=payload.rating)
        if not rated:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found or not resolved")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Submit rating failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit rating")


@router.post("/{complaint_id}/attachments")
async def upload_attachment(
    complaint_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Upload an attachment to a complaint (optional, max 10MB)"""
    try:
        # Validate file size
        content = await file.read()
        if len(content) > FileLimits.MAX_ATTACHMENT_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size exceeds {FileLimits.MAX_ATTACHMENT_SIZE_BYTES // FileLimits.MB}MB limit"
            )

        url = await service.upload_attachment(
            complaint_id=complaint_id,
            user_id=user_id,
            file_content=content,
            file_name=file.filename or "attachment"
        )
        if not url:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        return {"success": True, "url": url}
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid request")
    except Exception as e:
        logger.exception("Upload attachment failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to upload attachment")


@router.post("/admin/{complaint_id}/resolve")
async def admin_resolve_complaint(
    complaint_id: str,
    payload: dict,
    admin_user: UserModel = Depends(require_admin_role),
):
    """Admin/support endpoint to resolve a complaint and set adminResponse."""
    current_user_email = admin_user.email
    try:
        ok = await service.admin_update_status(
            complaint_id=complaint_id,
            status="resolved",
            admin_email=current_user_email,
            admin_response=str(payload.get("adminResponse") or ""),
            comment=str(payload.get("comment") or "Resolved by support"),
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Admin resolve failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resolve complaint")


@router.post("/admin/{complaint_id}/status")
async def admin_set_status(
    complaint_id: str,
    payload: dict,
    admin_user: UserModel = Depends(require_admin_role),
):
    """Admin/support endpoint to change status (pending|in_progress|resolved|rejected) and optionally set adminResponse."""
    current_user_email = admin_user.email
    new_status = str(payload.get("status") or "").strip().lower()
    if new_status not in {"pending", "in_progress", "in progress", "resolved", "rejected"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status")
    normalized = "in_progress" if new_status == "in progress" else new_status
    try:
        ok = await service.admin_update_status(
            complaint_id=complaint_id,
            status=normalized,
            admin_email=current_user_email,
            admin_response=str(payload.get("adminResponse") or ""),
            comment=str(payload.get("comment") or f"Status updated to {normalized}"),
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
        return {"ok": True}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Admin status update failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update complaint status")


@router.get("/admin", response_model=list[ComplaintResponseItem])
async def admin_list_complaints(
    admin_user: UserModel = Depends(require_admin_role),
    limit: int = 50,
    offset: int = 0,
    status_filter: Optional[str] = None,
    q: Optional[str] = None,
):
    """Admin/support endpoint to list complaints as a ticket queue."""
    try:
        items = await service.admin_list_complaints(limit=limit, offset=offset, status=status_filter, q=q)
        return JSONResponse(status_code=status.HTTP_200_OK, content=items)
    except Exception:
        logger.exception("Admin list complaints failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load complaints")
