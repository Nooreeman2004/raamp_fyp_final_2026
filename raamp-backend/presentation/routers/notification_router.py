from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from typing import List, Optional
from application.services.notification_service import NotificationService, manager
from presentation.schemas.notification_schemas import (
    NotificationResponse, NotificationListResponse, NotificationCreateRequest
)
from presentation.routers.auth_router import get_current_user_email
from infrastructure.database.models.notification_model import NotificationType
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])
service = NotificationService()

# --- Internal / Admin / Development ---
@router.post("", response_model=None)
async def create_notification(
    request: NotificationCreateRequest,
    current_user_email: str = Depends(get_current_user_email)
    # real production would likely restrict this to system/internal calls or service-to-service
):
    """
    Create a notification manually (or via system call).
    Triggers WebSocket push if user connects.
    """
    notification = await service.create_and_send(
        user_id=request.user_id,
        type=request.type,
        title=request.title,
        message=request.message,
        related_entity_id=request.related_entity_id,
        metadata=request.metadata or {}
    )
    if not notification:
         # Suppressed (consistent 200 shape; not an error)
         return JSONResponse(
             status_code=status.HTTP_200_OK,
             content={"suppressed": True, "message": "Notification suppressed by user preferences"},
         )
         
    return notification

# --- User Endpoints ---

@router.get("", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = 50,
    offset: int = 0,
    unread_only: bool = False,
    current_user_email: str = Depends(get_current_user_email)
):
    """Get list of notifications for the current user."""
    notifications = await service.get_user_notifications(current_user_email, limit, offset, unread_only)
    unread_count = await service.get_unread_count(current_user_email)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@router.get("/unread/count")
async def get_unread_count(
    current_user_email: str = Depends(get_current_user_email)
):
    """Get count of unread notifications."""
    count = await service.get_unread_count(current_user_email)
    return {"count": count}

@router.patch("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(
    notification_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Mark a specific notification as read."""
    notification = await service.mark_read(notification_id, current_user_email)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    return notification

@router.post("/read-all")
async def mark_all_as_read(
    current_user_email: str = Depends(get_current_user_email)
):
    """Mark all notifications as read."""
    count = await service.mark_all_read(current_user_email)
    return {"success": True, "count": count}


@router.delete("/all")
async def delete_all_notifications(
    current_user_email: str = Depends(get_current_user_email)
):
    """Delete all notifications for the current user."""
    deleted = await service.delete_all(current_user_email)
    return {"success": True, "deleted": deleted}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user_email: str = Depends(get_current_user_email)
):
    """Delete a notification."""
    success = await service.delete(notification_id, current_user_email)
    if not success:
         raise HTTPException(status_code=404, detail="Notification not found")
    return {"success": True}

# --- WebSocket ---

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(None), # Ideally passed via Query param since headers are hard in WS
):
    """
    Real-time notification socket.
    """
    # Accept connection first to avoid 403 handshake rejection
    await websocket.accept()
    
    # Simple Token Validation Logic (supports query param, Authorization header, or cookie)
    user_email = None
    try:
         from application.services.jwt_service import JWTService
         jwt_service = JWTService()
         auth_token = token
         if not auth_token:
             auth_header = websocket.headers.get("authorization")
             if auth_header and auth_header.lower().startswith("bearer "):
                 auth_token = auth_header.split(" ", 1)[1].strip()
         if not auth_token:
             # cookie auth: align with main auth system
             auth_token = websocket.cookies.get("access_token")

         if auth_token:
             # JWTService.verify_token returns the decoded payload dict
             payload = jwt_service.verify_token(auth_token)
             if payload:
                 user_email = payload.get("email")
                 logger.info("Notifications WS auth success for %s", user_email)
             else:
                 logger.warning("Notifications WS auth failed: invalid token")
         else:
             logger.warning("Notifications WS auth failed: no token provided")
    except Exception as e:
        logger.warning("Notifications WS auth exception: %s", str(e))
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    if not user_email:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Connect – Now that handshake is accepted and auth passed, we register it
    await manager.connect(websocket, user_email)
    
    try:
        while True:
            # Keep alive / listen for client messages (e.g. "mark_read")
            data = await websocket.receive_text()
            # We can handle client-originated events here if needed
            # E.g. await manager.process_client_message(data, user_email)
            pass 
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_email)
    except Exception as e:
        logger.warning("Notifications WS error: %s", str(e))
        manager.disconnect(websocket, user_email)
