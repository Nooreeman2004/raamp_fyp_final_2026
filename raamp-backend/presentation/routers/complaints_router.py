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
from presentation.routers.auth_router import get_current_user_id
from fastapi.responses import JSONResponse
from typing import Optional

router = APIRouter(prefix="/api/complaints", tags=["complaints"])
service = ComplaintService()


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/user", response_model=list[ComplaintResponseItem])
async def get_user_complaints(user_id: str = Depends(get_current_user_id)):
    """Get all complaints for the authenticated user"""
    try:
        complaints = await service.get_complaints_for_user(user_id)
        return JSONResponse(status_code=status.HTTP_200_OK, content=complaints)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/{complaint_id}/attachments")
async def upload_attachment(
    complaint_id: str,
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id)
):
    """Upload an attachment to a complaint (optional, max 10MB)"""
    try:
        # Validate file size (10MB max)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 10MB limit")

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
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
