from fastapi import APIRouter, Depends, HTTPException, status, Request
from presentation.schemas.onboarding_schemas import OnboardingStatusResponse, GoogleConnectRequest
from application.services.onboarding_service import OnboardingService
from presentation.routers.auth_router import get_current_user_email
from fastapi.responses import RedirectResponse
import httpx
from fastapi.responses import HTMLResponse
import logging
from config import settings as cfg
import httpx

router = APIRouter(prefix="/api/profile/onboarding", tags=["onboarding"])
service = OnboardingService()


@router.post("", response_model=OnboardingStatusResponse)
async def post_onboarding_status(current_user_email: str = Depends(get_current_user_email)):
    status_obj = await service.get_onboarding_status(current_user_email)
    if status_obj.get("completed"):
        # mark completed
        await service.mark_completed(current_user_email)
        # respond with completed + redirect to business setup
        return {"completed": True, "missing": {k: False for k in status_obj.get("missing", {})}, "redirect": "/dashboard"}
    return status_obj


@router.get("")
async def get_onboarding_status_root(current_user_email: str = Depends(get_current_user_email)):
    """GET handler for /api/profile/onboarding - same as /status"""
    status_obj = await service.get_onboarding_status(current_user_email)
    missing = status_obj.get("missing", {})
    facebook_connected = not bool(missing.get("facebook", True))
    instagram_connected = not bool(missing.get("instagram", True))
    google_maps_connected = not bool(missing.get("google_maps", True))
    ready = facebook_connected and instagram_connected and google_maps_connected
    redirect = "/dashboard" if ready else None
    return {
        "facebook_connected": facebook_connected,
        "instagram_connected": instagram_connected,
        "google_maps_connected": google_maps_connected,
        "ready_to_continue": ready,
        "redirect": redirect
    }


@router.get("/status")
async def get_onboarding_status(current_user_email: str = Depends(get_current_user_email)):
        """Return a simple onboarding status shape expected by the frontend.

        Response shape:
        {
            "facebook_connected": bool,
            "instagram_connected": bool,
            "google_maps_connected": bool,
            "ready_to_continue": bool,
            "redirect": Optional[str]
        }
        """
        status_obj = await service.get_onboarding_status(current_user_email)
        missing = status_obj.get("missing", {})
        facebook_connected = not bool(missing.get("facebook", True))
        instagram_connected = not bool(missing.get("instagram", True))
        google_maps_connected = not bool(missing.get("google_maps", True))
        ready = facebook_connected and instagram_connected and google_maps_connected
        redirect = "/dashboard" if ready else None
        return {
                "facebook_connected": facebook_connected,
                "instagram_connected": instagram_connected,
                "google_maps_connected": google_maps_connected,
                "ready_to_continue": ready,
                "redirect": redirect,
        }


@router.get("/facebook/auth")
async def facebook_auth(current_user_email: str = Depends(get_current_user_email)):
    # create a per-user OAuth state and build the FB auth url
    state = await service.create_oauth_state(current_user_email)
    url = service.build_facebook_oauth_url(current_user_email, state=state)
    return RedirectResponse(url)


@router.get("/facebook/callback")
async def facebook_callback(
    request: Request,
    code: str = None,
    state: str = None,
    error: str = None,
    error_code: str = None,
    error_message: str = None,
    error_reason: str = None,
):
    # Facebook sends error params instead of code when the user denies or there's a config issue
    if error or error_code:
        detail = error_message or error_reason or error or f"Facebook OAuth error (code: {error_code})"
        logging.warning(f"Facebook OAuth error redirect: error={error}, error_code={error_code}, message={error_message}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code")
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state")

    # Try to obtain current user from cookie; if unavailable, fall back to resolving
    # the user via the stored OAuth state token so the callback works even when
    # the browser doesn't send the auth cookie (common with cross-site redirects).
    current_user_email = None
    from fastapi import HTTPException as FastAPIHTTPException
    try:
        # `get_current_user_email` will raise HTTPException if not authenticated
        current_user_email = await get_current_user_email(request)
        # validate and consume the state for this user
        valid = await service.validate_oauth_state(current_user_email, state)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")
    except FastAPIHTTPException:
        # No auth cookie or invalid token — resolve user by state token directly
        user_by_state = await service.oauth_repo.validate_and_consume_by_state(state)
        if not user_by_state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired OAuth state")
        current_user_email = user_by_state

    try:
        token_data = await service.exchange_fb_code_for_token(code)
    except Exception as e:
        # provide a clearer message for debugging/token exchange failures
        logging.exception("Facebook token exchange failed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"FB token exchange failed: {e}")

    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token returned from FB")
    # fetch pages
    pages = []
    try:
        pages = await service.fetch_fb_pages(access_token)
    except Exception:
        pages = []

    # fetch fb user id
    fb_user_id = None
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("https://graph.facebook.com/v22.0/me", params={"access_token": access_token})
            r.raise_for_status()
            fb_user_id = r.json().get("id")
    except Exception:
        fb_user_id = None

    # store connection
    await service.store_facebook_connection(current_user_email, access_token, fb_user_id=fb_user_id, fb_pages=pages)
    # redirect to frontend onboarding UI (allow SPA to pick up state and show UI)
    # Redirect to a backend-hosted success page which links back to the SPA.
    # This avoids browser-level "site can't be reached" errors when the SPA dev server
    # is not running, and avoids returning a JSON 401 from protected backend routes.
    url = "/api/profile/onboarding/success"
    return RedirectResponse(url=url)


@router.post("/facebook/disconnect")
@router.delete("/facebook/disconnect")
async def facebook_disconnect(current_user_email: str = Depends(get_current_user_email)):
    """Disconnect Facebook account to allow re-authentication with updated permissions."""
    try:
        logging.info(f"Attempting to disconnect Facebook for user: {current_user_email}")
        
        # Delete from Facebook repository
        deleted_fb = await service.facebook_repo.delete_by_user_id(current_user_email)
        logging.info(f"Facebook account deleted: {deleted_fb}")
        
        # Also delete Instagram since it depends on Facebook
        deleted_ig = await service.instagram_repo.delete_by_user_id(current_user_email)
        logging.info(f"Instagram account deleted: {deleted_ig}")
        
        # Update user connection flags
        await service.user_repo.update_connection_flags(current_user_email, facebook=False, instagram=False)
        logging.info(f"Facebook & Instagram connection flags updated to False for {current_user_email}")
        
        return {"success": True, "message": "Facebook disconnected successfully. Instagram also disconnected."}
    except Exception as e:
        logging.exception(f"Failed to disconnect Facebook for {current_user_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to disconnect Facebook: {str(e)}"
        )


@router.post("/instagram/disconnect")
@router.delete("/instagram/disconnect")
async def instagram_disconnect(current_user_email: str = Depends(get_current_user_email)):
    """Disconnect Instagram account."""
    try:
        logging.info(f"Attempting to disconnect Instagram for user: {current_user_email}")
        
        # Delete from Instagram repository
        deleted_ig = await service.instagram_repo.delete_by_user_id(current_user_email)
        logging.info(f"Instagram account deleted: {deleted_ig}")
        
        # Update user connection flags
        await service.user_repo.update_connection_flags(current_user_email, instagram=False)
        logging.info(f"Instagram connection flag updated to False for {current_user_email}")
        
        return {"success": True, "message": "Instagram disconnected successfully."}
    except Exception as e:
        logging.exception(f"Failed to disconnect Instagram for {current_user_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Failed to disconnect Instagram: {str(e)}"
        )


@router.post("/google/disconnect")
async def google_disconnect(current_user_email: str = Depends(get_current_user_email)):
    """Disconnect Google Business / Clear Location Data (via Flags only, preserves Business Setup)."""
    try:
        # We don't delete the BusinessModel as that is core profile data, 
        # but we can clear the Google Business specific repo if it exists
        # and update the flags.
        await service.google_repo.delete_by_user_id(current_user_email)
        await service.user_repo.update_connection_flags(current_user_email, google_maps=False)
        return {"success": True, "message": "Google Business disconnected."}
    except Exception as e:
        logging.error(f"Failed to disconnect Google for {current_user_email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to disconnect Google")


@router.get("/success", response_class=HTMLResponse)
async def onboarding_success():
        """Simple HTML page shown after OAuth flows complete.

        Provides a link back to the frontend SPA (if running) and a friendly message.
        """
        from config import settings as cfg
        frontend = str(getattr(cfg, 'FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        html = f"""
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <title>Connection Successful - RAAMP</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                <style>
                    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                    body {{
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, hsl(200, 50%, 10%) 0%, hsl(200, 45%, 15%) 50%, hsl(180, 30%, 12%) 100%);
                        color: #f1f5f9;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }}
                    .container {{
                        text-align: center;
                        max-width: 480px;
                        width: 100%;
                    }}
                    .card {{
                        background: linear-gradient(145deg, rgba(11, 22, 32, 0.9), rgba(7, 16, 24, 0.95));
                        border: 1px solid rgba(0, 153, 153, 0.2);
                        border-radius: 16px;
                        padding: 40px 32px;
                        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 60px rgba(0, 153, 153, 0.1);
                        backdrop-filter: blur(10px);
                    }}
                    .icon-container {{
                        width: 80px;
                        height: 80px;
                        background: linear-gradient(135deg, rgba(0, 153, 153, 0.2), rgba(0, 153, 153, 0.1));
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        margin: 0 auto 24px;
                        animation: pulse 2s ease-in-out infinite;
                    }}
                    @keyframes pulse {{
                        0%, 100% {{ box-shadow: 0 0 0 0 rgba(0, 153, 153, 0.4); }}
                        50% {{ box-shadow: 0 0 0 15px rgba(0, 153, 153, 0); }}
                    }}
                    .checkmark {{
                        width: 40px;
                        height: 40px;
                        stroke: #00cccc;
                        stroke-width: 3;
                        fill: none;
                        animation: draw 0.6s ease-out forwards;
                    }}
                    @keyframes draw {{
                        from {{ stroke-dasharray: 100; stroke-dashoffset: 100; }}
                        to {{ stroke-dashoffset: 0; }}
                    }}
                    h1 {{
                        font-size: 1.75rem;
                        font-weight: 700;
                        margin-bottom: 12px;
                        background: linear-gradient(135deg, #00cccc, #00aaaa);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                    }}
                    p {{
                        color: #94a3b8;
                        line-height: 1.6;
                        margin-bottom: 8px;
                    }}
                    .button {{
                        display: inline-flex;
                        align-items: center;
                        gap: 8px;
                        margin-top: 24px;
                        padding: 14px 28px;
                        background: linear-gradient(135deg, #009999, #007777);
                        color: #ffffff;
                        border: none;
                        border-radius: 10px;
                        text-decoration: none;
                        font-weight: 600;
                        font-size: 1rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 15px rgba(0, 153, 153, 0.3);
                    }}
                    .button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 8px 25px rgba(0, 153, 153, 0.4);
                        background: linear-gradient(135deg, #00aaaa, #008888);
                    }}
                    .hint {{
                        margin-top: 20px;
                        font-size: 0.8rem;
                        color: #64748b;
                    }}
                    .hint code {{
                        background: rgba(0, 153, 153, 0.1);
                        padding: 2px 6px;
                        border-radius: 4px;
                        font-family: 'Fira Code', monospace;
                    }}
                    .logo {{
                        width: 60px;
                        height: 60px;
                        margin-bottom: 20px;
                        opacity: 0.9;
                    }}
                </style>
                <script>
                    // Notify parent window of success
                    if (window.opener && !window.opener.closed) {{
                        window.opener.postMessage({{ provider: 'facebook', success: true }}, '*');
                    }}
                </script>
            </head>
            <body>
                <div class="container">
                    <div class="card">
                        <div class="icon-container">
                            <svg class="checkmark" viewBox="0 0 52 52">
                                <path d="M14 27l10 10 16-20" stroke-linecap="round" stroke-linejoin="round"/>
                            </svg>
                        </div>
                        <h1>Connection Successful!</h1>
                        <p>Your account has been connected to RAAMP successfully.</p>
                        <p>You can now return to the application to continue your setup.</p>
                        <a class="button" href="{frontend}/profile/onboarding">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M19 12H5M12 19l-7-7 7-7"/>
                            </svg>
                            Return to RAAMP
                        </a>
                        <p class="hint">This window will close automatically, or you can close it manually.</p>
                    </div>
                </div>
                <script>
                    // Auto-close after a short delay
                    setTimeout(() => {{
                        try {{ window.close(); }} catch(e) {{}}
                    }}, 3000);
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)



@router.get("/instagram/auth", response_class=HTMLResponse)
async def instagram_auth_popup(request: Request):
        """Popup page that lists Facebook pages and allows linking the Instagram business account.

        This runs on the backend origin so requests to `/api/profile/onboarding/*` will include
        the auth cookie. On success it posts a message to the opener window so the SPA can
        react immediately.
        """
        # Check if user is authenticated - if not, show error page
        try:
            current_user_email = await get_current_user_email(request)
        except Exception as e:
            return HTMLResponse(content="""
            <!doctype html>
            <html lang="en">
                <head>
                    <meta charset="utf-8" />
                    <title>Authentication Required - RAAMP</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                    <style>
                        * { margin: 0; padding: 0; box-sizing: border-box; }
                        body {
                            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                            background: linear-gradient(135deg, hsl(200, 50%, 10%) 0%, hsl(200, 45%, 15%) 50%, hsl(180, 30%, 12%) 100%);
                            color: #f1f5f9;
                            min-height: 100vh;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            padding: 20px;
                        }
                        .card {
                            background: linear-gradient(145deg, rgba(11, 22, 32, 0.9), rgba(7, 16, 24, 0.95));
                            border: 1px solid rgba(239, 68, 68, 0.3);
                            border-radius: 16px;
                            padding: 40px 32px;
                            max-width: 420px;
                            text-align: center;
                            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                        }
                        .icon-container {
                            width: 70px;
                            height: 70px;
                            background: rgba(239, 68, 68, 0.1);
                            border-radius: 50%;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            margin: 0 auto 20px;
                        }
                        h2 {
                            font-size: 1.5rem;
                            font-weight: 700;
                            color: #f87171;
                            margin-bottom: 12px;
                        }
                        p { color: #94a3b8; line-height: 1.6; margin-bottom: 8px; }
                        .button {
                            display: inline-flex;
                            align-items: center;
                            gap: 8px;
                            margin-top: 20px;
                            padding: 12px 24px;
                            background: linear-gradient(135deg, #009999, #007777);
                            color: #fff;
                            border: none;
                            border-radius: 10px;
                            font-weight: 600;
                            cursor: pointer;
                            transition: all 0.3s ease;
                        }
                        .button:hover { transform: translateY(-2px); background: linear-gradient(135deg, #00aaaa, #008888); }
                    </style>
                </head>
                <body>
                    <div class="card">
                        <div class="icon-container">
                            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="8" x2="12" y2="12"/>
                                <line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                        </div>
                        <h2>Authentication Required</h2>
                        <p>You must be logged in to RAAMP to connect Instagram.</p>
                        <p>Please ensure you are logged in and try again.</p>
                        <button class="button" onclick="window.close()">Close Window</button>
                    </div>
                </body>
            </html>
            """, status_code=401)
        
        from config import settings as cfg
        frontend = str(getattr(cfg, 'FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        html = """
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <title>Link Instagram - RAAMP</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background: linear-gradient(135deg, hsl(200, 50%, 10%) 0%, hsl(200, 45%, 15%) 50%, hsl(180, 30%, 12%) 100%);
                        color: #f1f5f9;
                        min-height: 100vh;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 20px;
                    }
                    .container { max-width: 520px; width: 100%; }
                    .card {
                        background: linear-gradient(145deg, rgba(11, 22, 32, 0.9), rgba(7, 16, 24, 0.95));
                        border: 1px solid rgba(0, 153, 153, 0.2);
                        border-radius: 16px;
                        padding: 32px;
                        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 60px rgba(0, 153, 153, 0.08);
                    }
                    .header {
                        display: flex;
                        align-items: center;
                        gap: 16px;
                        margin-bottom: 24px;
                        padding-bottom: 20px;
                        border-bottom: 1px solid rgba(0, 153, 153, 0.15);
                    }
                    .icon-container {
                        width: 56px;
                        height: 56px;
                        background: linear-gradient(135deg, #E1306C, #C13584, #833AB4);
                        border-radius: 14px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        flex-shrink: 0;
                    }
                    h2 {
                        font-size: 1.4rem;
                        font-weight: 700;
                        color: #f1f5f9;
                        margin-bottom: 4px;
                    }
                    .subtitle { color: #64748b; font-size: 0.9rem; }
                    #list { margin-top: 8px; }
                    .loading {
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        padding: 40px 20px;
                        color: #94a3b8;
                    }
                    .spinner {
                        width: 40px;
                        height: 40px;
                        border: 3px solid rgba(0, 153, 153, 0.2);
                        border-top-color: #00cccc;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                        margin-bottom: 16px;
                    }
                    @keyframes spin { to { transform: rotate(360deg); } }
                    .page {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        padding: 16px;
                        background: rgba(0, 153, 153, 0.05);
                        border: 1px solid rgba(0, 153, 153, 0.1);
                        border-radius: 12px;
                        margin-bottom: 10px;
                        transition: all 0.2s ease;
                    }
                    .page:hover {
                        background: rgba(0, 153, 153, 0.1);
                        border-color: rgba(0, 153, 153, 0.2);
                    }
                    .page-info { flex: 1; min-width: 0; }
                    .page-name {
                        font-weight: 600;
                        color: #f1f5f9;
                        margin-bottom: 4px;
                        white-space: nowrap;
                        overflow: hidden;
                        text-overflow: ellipsis;
                    }
                    .page-id { font-size: 0.8rem; color: #64748b; font-family: 'Fira Code', monospace; }
                    .btn {
                        padding: 10px 20px;
                        background: linear-gradient(135deg, #009999, #007777);
                        color: #fff;
                        border: none;
                        border-radius: 8px;
                        font-weight: 600;
                        font-size: 0.9rem;
                        cursor: pointer;
                        transition: all 0.3s ease;
                        white-space: nowrap;
                    }
                    .btn:hover:not(:disabled) {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 15px rgba(0, 153, 153, 0.4);
                        background: linear-gradient(135deg, #00aaaa, #008888);
                    }
                    .btn:disabled { opacity: 0.7; cursor: not-allowed; transform: none; }
                    .btn-secondary {
                        background: transparent;
                        border: 1px solid rgba(0, 153, 153, 0.4);
                        color: #00cccc;
                    }
                    .btn-secondary:hover:not(:disabled) {
                        background: rgba(0, 153, 153, 0.1);
                        box-shadow: none;
                    }
                    .error-box {
                        padding: 20px;
                        background: rgba(239, 68, 68, 0.1);
                        border: 1px solid rgba(239, 68, 68, 0.3);
                        border-radius: 12px;
                        color: #fca5a5;
                    }
                    .error-box strong { color: #f87171; display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
                    .error-box ul { margin: 12px 0; padding-left: 24px; }
                    .error-box li { margin: 4px 0; }
                    .success-box {
                        padding: 20px;
                        background: rgba(0, 153, 153, 0.1);
                        border: 1px solid rgba(0, 153, 153, 0.3);
                        border-radius: 12px;
                        color: #5eead4;
                        display: flex;
                        align-items: center;
                        gap: 12px;
                    }
                    .success-box svg { flex-shrink: 0; }
                    .empty-state {
                        text-align: center;
                        padding: 30px 20px;
                        color: #94a3b8;
                    }
                    .empty-state svg { margin-bottom: 16px; opacity: 0.5; }
                    .hint {
                        margin-top: 16px;
                        font-size: 0.8rem;
                        color: #64748b;
                        text-align: center;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="card">
                        <div class="header">
                            <div class="icon-container">
                                <svg width="28" height="28" viewBox="0 0 24 24" fill="white">
                                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
                                </svg>
                            </div>
                            <div>
                                <h2>Link Instagram Account</h2>
                                <p class="subtitle">Select a Facebook Page to connect</p>
                            </div>
                        </div>
                        <div id="list">
                            <div class="loading">
                                <div class="spinner"></div>
                                <span>Loading your pages...</span>
                            </div>
                        </div>
                        <p class="hint">This window will close automatically when linking completes.</p>
                    </div>
                </div>

                <script>
                    function reconnectFacebook(){
                        if(window.opener && !window.opener.closed){
                            window.opener.postMessage({
                                provider:'facebook',
                                action:'reconnect',
                                message:'Please reconnect Facebook with all required permissions'
                            }, '*');
                        }
                        try{ window.close(); }catch(e){
                            alert('Please close this window and click "Connect Facebook" again.');
                        }
                    }
                    
                    async function checkPermissions(){
                        try{
                            const permResp = await fetch('/api/profile/connections/facebook/granted-scopes', {
                                credentials: 'include'
                            });
                            if(permResp.ok){
                                const permData = await permResp.json();
                                const grantedScopes = (permData.granted_scopes || []).map(s => s.toLowerCase());
                                const required = ['instagram_basic'];
                                const canon = (n) => ({
                                    'instagram_business_basic':'instagram_basic',
                                    'instagram_business_manage_messages':'instagram_manage_messages',
                                    'instagram_business_manage_comments':'instagram_manage_comments',
                                    'instagram_business_content_publish':'instagram_content_publish',
                                }[n] || n);
                                const grantedCanon = new Set(grantedScopes.map(canon));
                                const missing = required.filter(s => !grantedCanon.has(canon(s)));
                                if(missing.length > 0){
                                    const container = document.getElementById('list');
                                    container.innerHTML = `
                                        <div class="error-box">
                                            <strong>
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                                </svg>
                                                Missing Required Permissions
                                            </strong>
                                            <p>Your Facebook connection is missing these permissions:</p>
                                            <ul>${missing.map(m => '<li>' + m + '</li>').join('')}</ul>
                                            <button class="btn" onclick="reconnectFacebook()" style="margin-top:16px;width:100%">
                                                Reconnect Facebook
                                            </button>
                                            <p style="margin-top:12px;font-size:13px;color:#94a3b8">This will close this window and start the reconnection process.</p>
                                        </div>
                                    `;
                                    if(window.opener && !window.opener.closed){
                                        window.opener.postMessage({
                                            provider:'instagram', 
                                            success:false, 
                                            error:'Missing Facebook permissions: ' + missing.join(', '),
                                            needsReconnect: true
                                        }, '*');
                                    }
                                    return false;
                                }
                            }
                        }catch(e){
                            console.warn('Could not check permissions:', e);
                        }
                        return true;
                    }
                    
                    async function fetchPages(){
                        try{
                            const hasPermissions = await checkPermissions();
                            if(!hasPermissions) return;
                            
                            const r = await fetch('/api/profile/onboarding/instagram/pages', {
                                credentials: 'include'
                            });
                            
                            if(!r.ok) {
                                const errorData = await r.json().catch(() => ({}));
                                const detail = errorData.detail || '';
                                
                                // Check if Facebook is not connected
                                if(r.status === 400 && detail.includes('Facebook not connected')) {
                                    const container = document.getElementById('list');
                                    container.innerHTML = `
                                        <div class="error-box">
                                            <strong>
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                                </svg>
                                                Facebook Not Connected
                                            </strong>
                                            <p style="margin-top:8px">You need to connect Facebook first before linking Instagram.</p>
                                            <p style="margin-top:8px;font-size:0.85rem;color:#94a3b8">Instagram Business accounts are linked through Facebook Pages.</p>
                                            <button class="btn" onclick="window.close()" style="margin-top:16px">
                                                Close & Connect Facebook First
                                            </button>
                                        </div>
                                    `;
                                    return;
                                }
                                
                                // Check if token expired (401)
                                if(r.status === 401 || detail.includes('expired') || detail.includes('reconnect')) {
                                    const container = document.getElementById('list');
                                    container.innerHTML = `
                                        <div class="error-box">
                                            <strong>
                                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                                </svg>
                                                Facebook Token Expired
                                            </strong>
                                            <p style="margin-top:8px">Your Facebook connection has expired and needs to be refreshed.</p>
                                            <p style="margin-top:8px;font-size:0.85rem;color:#94a3b8">Please reconnect Facebook to get a fresh access token.</p>
                                            <button class="btn" onclick="reconnectFacebook()" style="margin-top:16px;width:100%">
                                                Reconnect Facebook
                                            </button>
                                        </div>
                                    `;
                                    if(window.opener && !window.opener.closed){
                                        window.opener.postMessage({
                                            provider:'facebook', 
                                            action:'reconnect',
                                            message:'Facebook token expired. Please reconnect.'
                                        }, '*');
                                    }
                                    return;
                                }
                                
                                throw new Error(detail || 'Failed to load pages');
                            }
                            const j = await r.json();
                            const pages = j.pages || [];
                            const container = document.getElementById('list');
                            
                            if(!Array.isArray(pages) || pages.length===0){
                                container.innerHTML = `
                                    <div class="empty-state">
                                        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                                            <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                                            <line x1="9" y1="9" x2="15" y2="15"/>
                                            <line x1="15" y1="9" x2="9" y2="15"/>
                                        </svg>
                                        <p>No Facebook Pages found.</p>
                                        <p style="font-size:0.85rem;margin-top:8px">Ensure Facebook is connected and has pages with Instagram linked.</p>
                                    </div>
                                `;
                                return;
                            }
                            
                            container.innerHTML = '';
                            pages.forEach(p=>{
                                const el = document.createElement('div');
                                el.className = 'page';
                                el.innerHTML = `
                                    <div class="page-info">
                                        <div class="page-name">${p.name}</div>
                                        <div class="page-id">ID: ${p.id}</div>
                                    </div>
                                `;
                                const btn = document.createElement('button');
                                btn.className = 'btn';
                                btn.textContent = 'Link';
                                btn.onclick = async ()=>{
                                    btn.disabled = true;
                                    btn.textContent = 'Linking...';
                                    try{
                                        const a = await fetch(`/api/profile/onboarding/instagram/accounts?page_id=${p.id}`, {
                                            credentials: 'include'
                                        });
                                        if(!a.ok){
                                            let errorMsg = 'Link failed. ';
                                            try{
                                                const errData = await a.json();
                                                if(a.status === 403 && errData.detail){
                                                    if(typeof errData.detail === 'object' && errData.detail.missing){
                                                        errorMsg = `Missing permissions: ${errData.detail.missing.join(', ')}`;
                                                    } else if(typeof errData.detail === 'string'){
                                                        errorMsg = errData.detail;
                                                    }
                                                } else if(errData.detail){
                                                    errorMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail);
                                                }
                                            }catch(parseErr){
                                                errorMsg += 'Please ensure Instagram is linked to this Facebook Page.';
                                            }
                                            container.innerHTML = `
                                                <div class="error-box">
                                                    <strong>
                                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                                        </svg>
                                                        Connection Error
                                                    </strong>
                                                    <p style="margin-top:8px">${errorMsg}</p>
                                                    <button class="btn" onclick="reconnectFacebook()" style="margin-top:16px;width:100%">
                                                        Reconnect Facebook
                                                    </button>
                                                </div>
                                            `;
                                            if(window.opener && !window.opener.closed){
                                                window.opener.postMessage({provider:'instagram', success:false, error:errorMsg}, '*');
                                            }
                                            return;
                                        }
                                        if(window.opener && !window.opener.closed){
                                            window.opener.postMessage({provider:'instagram', success:true, page_id:p.id}, '*');
                                        }
                                        container.innerHTML = `
                                            <div class="success-box">
                                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#5eead4" stroke-width="2">
                                                    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                                                    <polyline points="22 4 12 14.01 9 11.01"/>
                                                </svg>
                                                <div>
                                                    <strong style="color:#5eead4">Instagram Linked Successfully!</strong>
                                                    <p style="font-size:0.9rem;margin-top:4px">You can close this window now.</p>
                                                </div>
                                            </div>
                                        `;
                                        setTimeout(()=>{ try{ window.close(); }catch(e){} }, 1500);
                                    }catch(err){
                                        btn.disabled = false;
                                        btn.textContent = 'Link';
                                        container.innerHTML = `
                                            <div class="error-box">
                                                <strong>
                                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                                        <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                                    </svg>
                                                    Connection Failed
                                                </strong>
                                                <p style="margin-top:8px">${err.message || 'Unable to link Instagram. Please try again.'}</p>
                                            </div>
                                        `;
                                    }
                                };
                                el.appendChild(btn);
                                container.appendChild(el);
                            });
                        }catch(e){
                            const container = document.getElementById('list');
                            const errorMsg = e.message || 'Unknown error';
                            container.innerHTML = `
                                <div class="error-box">
                                    <strong>
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                            <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                                        </svg>
                                        Unable to Load Pages
                                    </strong>
                                    <p style="margin-top:8px">${errorMsg}</p>
                                    <p style="margin-top:8px;font-size:0.85rem;color:#94a3b8">Please ensure Facebook is connected first.</p>
                                    <button class="btn btn-secondary" onclick="location.reload()" style="margin-top:16px">
                                        Try Again
                                    </button>
                                </div>
                            `;
                        }
                    }
                    fetchPages();
                </script>
            </body>
        </html>
        """
        return HTMLResponse(content=html)


@router.get("/instagram/pages")
async def instagram_pages(current_user_email: str = Depends(get_current_user_email)):
    fb = await service.facebook_repo.find_by_user_id(current_user_email)
    if not fb:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facebook not connected")
    # return pages annotated with whether they have a linked Instagram business account
    try:
        pages = await service.fetch_pages_with_ig(fb.access_token)
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error fetching pages with IG: {error_msg}")
        # Check if this is a token-related error
        if "400" in error_msg or "Invalid" in error_msg or "expired" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Facebook access token expired. Please reconnect Facebook."
            )
        # fallback to raw pages if the detailed check fails
        try:
            pages = await service.fetch_fb_pages(fb.access_token)
            # normalize shape
            pages = [{"id": p.get("id"), "name": p.get("name"), "has_instagram": False, "instagram": None} for p in pages]
        except Exception as e2:
            error_msg2 = str(e2)
            logging.error(f"Error fetching raw pages: {error_msg2}")
            if "400" in error_msg2 or "Invalid" in error_msg2 or "expired" in error_msg2.lower():
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, 
                    detail="Facebook access token expired. Please reconnect Facebook."
                )
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch pages: {error_msg2}")
    return {"pages": pages}


@router.get("/instagram/accounts")
async def instagram_accounts(page_id: str, current_user_email: str = Depends(get_current_user_email)):
    try:
        fb = await service.facebook_repo.find_by_user_id(current_user_email)
        if not fb:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facebook not connected")
        # Verify required permissions are granted on the stored user access token
        # Use official Instagram Graph permission names
        required = [
            "pages_show_list",
            "pages_read_engagement",
            "instagram_basic",
        ]
        try:
            missing = await service.missing_permissions(fb.access_token, required)
        except Exception as e:
            logging.error(f"Error checking permissions for {current_user_email}: {e}", exc_info=True)
            missing = []
        
        if missing:
            # log missing permission event for debugging/telemetry
            logging.warning("Missing FB permissions for user %s: %s", current_user_email, missing)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail={
                    "error": "missing_permissions", 
                    "missing": missing,
                    "message": f"Please reconnect Facebook to grant these permissions: {', '.join(missing)}"
                }
            )

        # find the page token from /me/accounts and use that page access token to query the page for IG linkage
        pages = await service.fetch_fb_pages(fb.access_token)
        page = next((p for p in pages if p.get("id") == page_id), None)
        if not page:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Page not found on your account")
        page_token = page.get("access_token")
        if not page_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to obtain page access token. Please re-authorize Facebook with required scopes.")

        ig = await service.fetch_ig_account_for_page(page_token, page_id)
        if not ig:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This page has no Instagram account linked.")
        # ig contains id of the business account; fetch details
        ig_id = ig.get("id") if isinstance(ig, dict) else ig
        ig_details = None
        try:
            ig_details = await service.fetch_ig_details(page_token, ig_id)
        except Exception:
            ig_details = None
        # store instagram connection with enhanced fields
        if ig_details:
            username = ig_details.get("username")
            profile_picture = ig_details.get("profile_picture_url")
            account_type = ig_details.get("account_type")
        else:
            username = None
            profile_picture = None
            account_type = None
        await service.store_instagram_connection(
            current_user_email, 
            ig_id, 
            username=username, 
            account_type=account_type, 
            linked_fb_page_id=page_id, 
            profile_picture_url=profile_picture,
            page_access_token=page_token,
            user_access_token=fb.access_token
        )
        return {"instagram_business_account": ig_details or ig}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error linking Instagram for {current_user_email}, page {page_id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to link Instagram: {str(e)}")


@router.post("/google-maps/connect")
async def google_maps_connect(payload: GoogleConnectRequest, current_user_email: str = Depends(get_current_user_email)):
    await service.store_google_business(current_user_email, business_name=payload.business_name, address=payload.address, latitude=payload.latitude, longitude=payload.longitude, place_id=payload.google_place_id)
    return {"success": True}


@router.post("/maps/search")
async def maps_search(payload: dict, current_user_email: str = Depends(get_current_user_email)):
    """Server-side search using Google Places Text Search to support clients without JS Maps."""
    try:
        logging.info(f"Maps search called: user={current_user_email}, payload={payload}")
        query = (payload.get('query') or '').strip()
        if not query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is required")
        key = getattr(cfg, 'GOOGLE_MAPS_API_KEY', '')
        logging.info(f"API key present: {bool(key)}, length: {len(key) if key else 0}")
        if not key:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server not configured with Google Maps API key")
        url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        params = {'query': query, 'key': key}
        logging.info(f"Calling Google Maps API...")
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
        logging.info(f"Google Maps response: status={data.get('status')}")
        
        # Check for API errors
        if data.get('status') != 'OK' and data.get('status') != 'ZERO_RESULTS':
            logging.error(f"Google Maps API error: {data.get('status')} - {data.get('error_message', 'No error message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail=f"Google Maps API error: {data.get('status')}"
            )
        
        results = []
        for item in data.get('results', []):
            loc = item.get('geometry', {}).get('location', {})
            results.append({
                'place_id': item.get('place_id'),
                'name': item.get('name'),
                'formatted_address': item.get('formatted_address') or item.get('vicinity'),
                'lat': loc.get('lat'),
                'lng': loc.get('lng')
            })
        logging.info(f"Returning {len(results)} results")
        return {'results': results}
    except Exception as e:
        logging.error(f"ERROR in maps_search: {type(e).__name__}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Search error: {str(e)}")


@router.post('/maps/confirm')
async def maps_confirm(payload: dict, current_user_email: str = Depends(get_current_user_email)):
    place_id = payload.get('place_id')
    if not place_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='place_id is required')
    key = getattr(cfg, 'GOOGLE_MAPS_API_KEY', '')
    if not key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server not configured with Google Maps API key")
    url = 'https://maps.googleapis.com/maps/api/place/details/json'
    params = {'place_id': place_id, 'key': key, 'fields': 'place_id,name,formatted_address,geometry'}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=10.0)
        r.raise_for_status()
        data = r.json()
    result = data.get('result', {})
    loc = result.get('geometry', {}).get('location', {})
    return {
        'place_id': result.get('place_id'),
        'name': result.get('name'),
        'formatted_address': result.get('formatted_address'),
        'lat': loc.get('lat'),
        'lng': loc.get('lng')
    }


@router.post('/maps/save')
async def maps_save(payload: dict, current_user_email: str = Depends(get_current_user_email)):
    # Expecting: place_id, name, address, optional lat/lng
    place_id = payload.get('place_id')
    name = payload.get('name')
    address = payload.get('address')
    lat = payload.get('lat')
    lng = payload.get('lng')
    if not place_id or not name or not address:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='place_id, name and address are required')
    try:
        await service.store_google_business(current_user_email, business_name=name, address=address, latitude=lat or 0.0, longitude=lng or 0.0, place_id=place_id)
    except Exception as e:
        logging.exception('Failed to save google business')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return {'success': True}
