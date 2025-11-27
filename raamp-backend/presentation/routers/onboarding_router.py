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
        return {"completed": True, "missing": {k: False for k in status_obj.get("missing", {})}, "redirect": "/profile/business-setup"}
    return status_obj


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
        redirect = "/profile/business-setup" if ready else None
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
async def facebook_callback(request: Request, code: str = None, state: str = None):
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



@router.get("/success", response_class=HTMLResponse)
async def onboarding_success():
        """Simple HTML page shown after OAuth flows complete.

        Provides a link back to the frontend SPA (if running) and a friendly message.
        """
        from config import settings as cfg
        frontend = str(getattr(cfg, 'FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>Onboarding Complete</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <style>body{{font-family:Arial,Helvetica,sans-serif;background:#0f1724;color:#cbd5e1;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}.card{{background:#071024;padding:24px;border-radius:8px;max-width:720px;text-align:center;box-shadow:0 10px 30px rgba(2,6,23,0.7)}}a.button{{display:inline-block;margin-top:16px;padding:10px 18px;background:#06b6d4;color:#032; border-radius:6px;text-decoration:none;font-weight:600}}</style>
            </head>
            <body>
                <div class="card">
                    <h1>Connection Successful</h1>
                    <p>Your account has been connected. You can return to the RAAMP application to continue setup.</p>
                    <p>If your frontend is running locally, click the button below to open the onboarding page.</p>
                    <a class="button" href="{frontend}/profile/onboarding">Open RAAMP Onboarding</a>
                    <p style="margin-top:12px;color:#9ca3af;font-size:13px">If the link does not work, ensure your frontend dev server is running (e.g. <code>npm run dev</code> in the frontend folder).</p>
                </div>
            </body>
        </html>
        """
        return HTMLResponse(content=html)



@router.get("/instagram/auth", response_class=HTMLResponse)
async def instagram_auth_popup():
        """Popup page that lists Facebook pages and allows linking the Instagram business account.

        This runs on the backend origin so requests to `/api/profile/onboarding/*` will include
        the auth cookie. On success it posts a message to the opener window so the SPA can
        react immediately.
        """
        from config import settings as cfg
        frontend = str(getattr(cfg, 'FRONTEND_URL', 'http://localhost:5173')).rstrip('/')
        html = """
        <!doctype html>
        <html>
            <head>
                <meta charset="utf-8" />
                <title>Link Instagram</title>
                <meta name="viewport" content="width=device-width, initial-scale=1" />
                <style>
                    body{{font-family:Arial,Helvetica,sans-serif;background:#071024;color:#cbd5e1;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}}
                    .card{{background:#0b1620;padding:20px;border-radius:10px;max-width:760px;width:94%}}
                    .page{{display:flex;align-items:center;justify-content:space-between;padding:10px;border-radius:8px;background:#071b24;margin-bottom:8px}}
                    .btn{{background:#06b6d4;color:#032;padding:8px 12px;border-radius:8px;text-decoration:none;font-weight:600}}
                </style>
            </head>
            <body>
                <div class="card">
                    <h2 style="margin-top:0">Select a Facebook Page to Link Instagram</h2>
                    <div id="list">Loading pages…</div>
                    <div style="margin-top:12px;color:#9ca3af;font-size:13px">This window will close automatically when linking completes.</div>
                </div>

                <script>
                    async function fetchPages(){
                        try{
                            const r = await fetch('/api/profile/onboarding/instagram/pages');
                            if(!r.ok) throw new Error('Failed to load pages');
                            const j = await r.json();
                            const pages = j.pages || [];
                            const container = document.getElementById('list');
                            if(!Array.isArray(pages) || pages.length===0){
                                container.innerHTML = '<div>No pages found. Ensure Facebook is connected and has pages.</div>';
                                return;
                            }
                            container.innerHTML = '';
                            pages.forEach(p=>{
                                const el = document.createElement('div');
                                el.className = 'page';
                                const left = document.createElement('div');
                                left.innerHTML = `<div style="font-weight:600">${p.name}</div><div style="font-size:12px;color:#9ca3af">${p.id}</div>`;
                                const right = document.createElement('div');
                                const btn = document.createElement('button');
                                btn.className = 'btn';
                                btn.textContent = 'Link';
                                btn.onclick = async ()=>{
                                    btn.disabled = true;
                                    btn.textContent = 'Linking…';
                                    try{
                                        const a = await fetch(`/api/profile/onboarding/instagram/accounts?page_id=${p.id}`);
                                        if(!a.ok) throw new Error('Link failed');
                                        // notify opener
                                        if(window.opener && !window.opener.closed){
                                            window.opener.postMessage({provider:'instagram', success:true, page_id:p.id}, '*');
                                        }
                                        container.innerHTML = '<div style="padding:12px;background:#06222b;border-radius:8px">Instagram linked successfully. You can close this window.</div>';
                                        setTimeout(()=>{ try{ window.close(); }catch(e){} }, 900);
                                    }catch(err){
                                        btn.disabled = false; btn.textContent = 'Link';
                                        alert('Link failed. Ensure the backend is running and you have permissions.');
                                    }
                                };
                                right.appendChild(btn);
                                el.appendChild(left);
                                el.appendChild(right);
                                container.appendChild(el);
                            });
                        }catch(e){
                            const container = document.getElementById('list');
                            container.innerHTML = '<div style="color:#f97373">Unable to load pages. Please ensure the backend is running and you are logged in.</div>';
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
    except Exception:
        # fallback to raw pages if the detailed check fails
        pages = await service.fetch_fb_pages(fb.access_token)
        # normalize shape
        pages = [{"id": p.get("id"), "name": p.get("name"), "has_instagram": False, "instagram": None} for p in pages]
    return {"pages": pages}


@router.get("/instagram/accounts")
async def instagram_accounts(page_id: str, current_user_email: str = Depends(get_current_user_email)):
    fb = await service.facebook_repo.find_by_user_id(current_user_email)
    if not fb:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Facebook not connected")
    # Verify required permissions are granted on the stored user access token
    required = ["instagram_basic", "business_management", "pages_read_engagement"]
    try:
        missing = await service.missing_permissions(fb.access_token, required)
    except Exception:
        missing = []
    if missing:
        # log missing permission event for debugging/telemetry
        logging.warning("Missing FB permissions for user %s: %s", current_user_email, missing)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "missing_permissions", "missing": missing})

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
    await service.store_instagram_connection(current_user_email, ig_id, username=username, account_type=account_type, linked_fb_page_id=page_id, profile_picture_url=profile_picture)
    return {"instagram_business_account": ig_details or ig}


@router.post("/google-maps/connect")
async def google_maps_connect(payload: GoogleConnectRequest, current_user_email: str = Depends(get_current_user_email)):
    await service.store_google_business(current_user_email, business_name=payload.business_name, address=payload.address, latitude=payload.latitude, longitude=payload.longitude, place_id=payload.google_place_id)
    return {"success": True}


@router.post("/maps/search")
async def maps_search(payload: dict, current_user_email: str = Depends(get_current_user_email)):
    """Server-side search using Google Places Text Search to support clients without JS Maps."""
    query = (payload.get('query') or '').strip()
    if not query:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query is required")
    key = getattr(cfg, 'GOOGLE_MAPS_API_KEY', '')
    if not key:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server not configured with Google Maps API key")
    url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
    params = {'query': query, 'key': key}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, params=params, timeout=10.0)
        r.raise_for_status()
        data = r.json()
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
    return {'results': results}


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
