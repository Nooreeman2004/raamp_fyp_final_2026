from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse, RedirectResponse
from presentation.routers.auth_router import get_current_user_email
from application.services.encryption_service import EncryptionService
from infrastructure.repositories.social_media_repository import SocialMediaRepository
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.repositories.oauth_state_repository import OAuthStateRepository
from application.services.onboarding_service import OnboardingService
from infrastructure.repositories.user_repository_impl import UserRepository
from config import settings as cfg
import httpx
from datetime import datetime, timedelta
import logging

router = APIRouter(prefix="/api/instagram", tags=["instagram"])
repo = SocialMediaRepository()
ig_repo = InstagramRepository()
oauth_repo = OAuthStateRepository()
user_repo = UserRepository()
onboarding_service = OnboardingService()


@router.get('/auth-url')
async def instagram_auth_url(current_user_email: str = Depends(get_current_user_email)):
    # generate CSRF-safe state and return FB OAuth URL
    # create a state token via the onboarding service helper (handles TTL)
    state = await onboarding_service.create_oauth_state(current_user_email)
    redirect_uri = f"{cfg.BACKEND_URL}/api/instagram/callback"
    scopes = [
        'pages_show_list',
        'pages_read_engagement',
        'instagram_business_basic',  # Required for username, profile info
        'instagram_business_manage_comments',
        'instagram_business_manage_messages',
        'instagram_business_content_publish',
    ]
    params = {
        'client_id': cfg.FACEBOOK_APP_ID,
        'redirect_uri': redirect_uri,
        'scope': ','.join(scopes),
        'state': state,
    }
    from urllib.parse import quote
    qs = '&'.join([f"{k}={quote(v)}" for k, v in params.items()])
    url = f"https://www.facebook.com/v22.0/dialog/oauth?{qs}"
    return JSONResponse({'auth_url': url})


@router.get('/callback')
async def instagram_callback(request: Request, code: str = None, state: str = None):
    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    # validate state and resolve user
    try:
        # try to resolve current user from request cookie
        current_user_email = await get_current_user_email(request)
        valid = await oauth_repo.validate_and_consume(current_user_email, state)
        if not valid:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid OAuth state')
    except Exception:
        # fallback: resolve by state only
        user_by_state = await oauth_repo.validate_and_consume_by_state(state)
        if not user_by_state:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid or expired OAuth state')
        current_user_email = user_by_state

    # Exchange code for short-lived token
    token_url = 'https://graph.facebook.com/v22.0/oauth/access_token'
    params = {
        'client_id': cfg.FACEBOOK_APP_ID,
        'redirect_uri': f"{cfg.BACKEND_URL}/api/instagram/callback",
        'client_secret': cfg.FACEBOOK_APP_SECRET,
        'code': code,
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(token_url, params=params, timeout=10.0)
        try:
            r.raise_for_status()
        except Exception:
            logging.exception("Failed to exchange code for token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token",
            )
        data = r.json()

    short_token = data.get('access_token')
    if not short_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No access token returned')

    # Exchange short-lived -> long-lived
    exch_url = 'https://graph.facebook.com/v22.0/oauth/access_token'
    exch_params = {
        'grant_type': 'fb_exchange_token',
        'client_id': cfg.FACEBOOK_APP_ID,
        'client_secret': cfg.FACEBOOK_APP_SECRET,
        'fb_exchange_token': short_token,
    }
    async with httpx.AsyncClient() as client:
        r2 = await client.get(exch_url, params=exch_params, timeout=10.0)
        r2.raise_for_status()
        exch = r2.json()

    long_token = exch.get('access_token')
    expires_in = exch.get('expires_in')
    expires_at = None
    if expires_in:
        expires_at = datetime.utcnow() + timedelta(seconds=int(expires_in))

    # fetch user's pages
    pages = []
    try:
        async with httpx.AsyncClient() as client:
            r3 = await client.get('https://graph.facebook.com/v22.0/me/accounts', params={'access_token': long_token}, timeout=10.0)
            r3.raise_for_status()
            pages = r3.json().get('data', [])
    except Exception:
        pages = []

    # find a page that has instagram_business_account
    chosen = None
    for p in pages:
        pid = p.get('id')
        page_token = p.get('access_token')
        if not pid or not page_token:
            continue
        try:
            async with httpx.AsyncClient() as client:
                r4 = await client.get(f'https://graph.facebook.com/v22.0/{pid}', params={'fields': 'instagram_business_account', 'access_token': page_token}, timeout=10.0)
                r4.raise_for_status()
                info = r4.json()
                ig = info.get('instagram_business_account')
                if ig:
                    chosen = {
                        'page_id': pid,
                        'page_name': p.get('name'),
                        'page_access_token': page_token,
                        'ig_business_id': ig.get('id') if isinstance(ig, dict) else ig,
                    }
                    break
        except Exception:
            continue

    if not chosen:
        # friendly message when none found
        return JSONResponse({'success': False, 'message': 'No Instagram Business account found. Please link your Instagram to one of your Facebook Pages and try again.'}, status_code=200)

    # encrypt tokens and store
    try:
        enc = EncryptionService()
    except Exception as e:
        logging.exception('Encryption service not configured')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Server encryption misconfiguration')

    encrypted_long = enc.encrypt(long_token)
    encrypted_page_token = enc.encrypt(chosen.get('page_access_token'))

    # Fetch Instagram profile details for username/profile picture
    ig_business_id = chosen.get('ig_business_id')
    username = None
    profile_picture_url = None
    account_type = None
    try:
        page_token = chosen.get('page_access_token')
        async with httpx.AsyncClient() as client:
            r = await client.get(
                f'https://graph.facebook.com/v22.0/{ig_business_id}',
                params={'fields': 'username,profile_picture_url,account_type', 'access_token': page_token},
                timeout=10.0
            )
            r.raise_for_status()
            ig_details = r.json()
            username = ig_details.get('username')
            profile_picture_url = ig_details.get('profile_picture_url')
            account_type = ig_details.get('account_type')
    except Exception as e:
        logging.warning(f'Could not fetch Instagram profile details: {e}')

    # Save to InstagramConnectionModel
    logging.info(f"Saving Instagram connection for {current_user_email}. Page Token Length: {len(encrypted_page_token) if encrypted_page_token else 'None'}, User Token Length: {len(encrypted_long) if encrypted_long else 'None'}")
    await ig_repo.create_or_update(
        current_user_email,
        ig_business_id=ig_business_id,
        page_access_token=encrypted_page_token,  # Store encrypted page token
        user_access_token=encrypted_long,         # Store encrypted user token
        username=username,
        account_type=account_type,
        linked_fb_page_id=chosen.get('page_id'),
        profile_picture_url=profile_picture_url,
        expires_at=expires_at
    )
    
    # Update User model connection flag
    await user_repo.update_connection_flags(current_user_email, instagram=True)
    logging.info(f'Instagram connected successfully for {current_user_email} - IG Business ID: {ig_business_id}, Username: {username}')

    # respond with success shape expected by frontend
    return JSONResponse({'success': True, 'message': 'Instagram connected successfully', 'pageName': chosen.get('page_name'), 'igBusinessId': ig_business_id})


@router.get('/status')
async def instagram_status(current_user_email: str = Depends(get_current_user_email)):
    doc = await ig_repo.find_by_user_id(current_user_email)
    if not doc or not doc.ig_business_id:
        return {'connected': False}
    return {'connected': True, 'username': doc.username, 'igBusinessId': doc.ig_business_id}


@router.post('/disconnect')
async def instagram_disconnect(current_user_email: str = Depends(get_current_user_email)):
    ok = await ig_repo.delete_by_user_id(current_user_email)
    # Update User model flag
    if ok:
        await user_repo.update_connection_flags(current_user_email, instagram=False)
        logging.info(f'Instagram disconnected for {current_user_email}')
    return {'success': ok}
