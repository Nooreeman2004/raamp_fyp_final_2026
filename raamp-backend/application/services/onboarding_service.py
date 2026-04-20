from typing import Dict, Any, Optional, List
import httpx
import secrets
import logging
from datetime import datetime, timedelta
from config import settings
from infrastructure.repositories.facebook_repository import FacebookRepository
from infrastructure.repositories.instagram_repository import InstagramRepository
from infrastructure.repositories.google_business_repository import GoogleBusinessRepository
from infrastructure.repositories.oauth_state_repository import OAuthStateRepository
from application.services.encryption_service import EncryptionService
from infrastructure.repositories.user_repository_impl import UserRepository


class OnboardingService:
    def __init__(self):
        self.facebook_repo = FacebookRepository()
        self.instagram_repo = InstagramRepository()
        self.google_repo = GoogleBusinessRepository()
        self.oauth_repo = OAuthStateRepository()
        self.user_repo = UserRepository()
        self.encryption_service = EncryptionService()

    async def get_onboarding_status(self, user_email: str) -> Dict[str, Any]:
        fb = await self.facebook_repo.find_by_user_id(user_email)
        ig = await self.instagram_repo.find_by_user_id(user_email)
        
        # Check BusinessRepository for Google Maps / Business Setup status (Single Source of Truth)
        from infrastructure.repositories.business_repository import BusinessRepository
        business_repo = BusinessRepository()
        
        # Resolve user_id from email since BusinessRepository uses user_id
        user = await self.user_repo.find_by_email(user_email)
        business = None
        if user:
            business = await business_repo.get_by_user_id(str(user.id))
        
        # Updated logic: Consider connected if we have valid coordinates, 
        # even if place_id is missing (e.g. manual pin drop)
        google_connected = False
        if business and business.latitude is not None and business.longitude is not None:
             # Ensure they are not default 0s if that's how they are initialized, though 0.0 is valid coordinate.
             # Assuming (0,0) is likely invalid/default for this app context if that's the issue, 
             # but strictly 'is not None' is safer for general float checks.
             # We also check if they are not 0.0 just in case defaults are 0.
             if business.latitude != 0.0 or business.longitude != 0.0:
                google_connected = True
        
        logging.info(f"Onboarding Status Check [{user_email}]: Business Found={bool(business)}, GoogleConnected={google_connected}, Lat={getattr(business, 'latitude', 'N/A')}, Lon={getattr(business, 'longitude', 'N/A')}")
        
        # Sync flags if needed
        if google_connected and user and not getattr(user, 'google_maps_connected', False):
             logging.info(f"Syncing google_maps_connected flag for {user_email}")
             await self.user_repo.update_connection_flags(user.email, google_maps=True)

        missing = {
            "facebook": fb is None,
            "instagram": ig is None or not getattr(ig, 'ig_business_id', None),
            "google_maps": not google_connected
        }

        completed = not any(missing.values())
        return {
            "completed": completed,
            "missing": missing
        }

    async def mark_completed(self, user_email: str):
        # mark profile_completed on user
        await self.user_repo.update_profile_completed(user_email, completed=True)

    async def create_oauth_state(self, user_email: str, ttl_minutes: int = 10) -> str:
        state = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
        await self.oauth_repo.create_state(user_email, state, expires_at=expires_at)
        return state

    def build_facebook_oauth_url(self, user_email: str, state: Optional[str] = None) -> str:
        # Allow configuring scopes via environment for dev vs production.
        # Use a conservative default suitable for development/test accounts.
        default_scopes = [
            "public_profile",
            "email",
            "pages_show_list",
            "pages_read_engagement",
            "pages_manage_metadata",
            "pages_manage_posts",  # Required for posting content to Facebook Pages
            # Official Instagram Graph API permissions (Business/Creator)
            "instagram_basic",
            "instagram_manage_comments",
            "instagram_manage_messages",
            "instagram_content_publish",
            "business_management",
            "ads_read",
            "ads_management",
        ]
        raw = getattr(settings, "FACEBOOK_OAUTH_SCOPES", None)
        if raw:
            # Accept either comma-separated string or list in settings
            if isinstance(raw, str):
                scopes = [s.strip() for s in raw.split(",") if s.strip()]
            elif isinstance(raw, (list, tuple)):
                scopes = list(raw)
            else:
                scopes = default_scopes
        else:
            scopes = default_scopes

        # Log the scopes being requested for debugging
        logging.info(f"Building Facebook OAuth URL for {user_email} with scopes: {','.join(scopes)}")
        logging.warning(f"If you see deprecated scope errors, update your Facebook App settings at: https://developers.facebook.com/apps/{settings.FACEBOOK_APP_ID}/app-review/permissions/")
        
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": f"{settings.BACKEND_URL}/api/profile/onboarding/facebook/callback",
            "scope": ",".join(scopes),
            "auth_type": "rerequest"  # Force FB to show permission dialog even if previously granted
        }
        if state:
            params["state"] = state
        # safe query string construction
        from urllib.parse import quote
        qs = "&".join([f"{k}={quote(v) if isinstance(v, str) else v}" for k, v in params.items()])
        return f"https://www.facebook.com/v22.0/dialog/oauth?{qs}"

    async def exchange_fb_code_for_token(self, code: str) -> Dict[str, Any]:
        url = "https://graph.facebook.com/v22.0/oauth/access_token"
        params = {
            "client_id": settings.FACEBOOK_APP_ID,
            "redirect_uri": f"{settings.BACKEND_URL}/api/profile/onboarding/facebook/callback",
            "client_secret": settings.FACEBOOK_APP_SECRET,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()

            # exchange short-lived for long-lived
            if "access_token" in data:
                exch_url = "https://graph.facebook.com/v22.0/oauth/access_token"
                exch_params = {
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.FACEBOOK_APP_ID,
                    "client_secret": settings.FACEBOOK_APP_SECRET,
                    "fb_exchange_token": data["access_token"],
                }
                r2 = await client.get(exch_url, params=exch_params, timeout=10.0)
                r2.raise_for_status()
                return r2.json()
            return data

    async def validate_oauth_state(self, user_email: str, state: str) -> bool:
        return await self.oauth_repo.validate_and_consume(user_email, state)

    async def fetch_fb_pages(self, access_token: str) -> List[Dict[str, Any]]:
        url = "https://graph.facebook.com/v22.0/me/accounts"
        params = {"access_token": access_token}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            return data.get("data", [])

    async def fetch_permissions(self, access_token: str) -> List[str]:
        """Return list of granted permissions for this access token."""
        url = "https://graph.facebook.com/v22.0/me/permissions"
        params = {"access_token": access_token}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            # Facebook returns permissions with status "granted" or "declined"
            perms = [p.get("permission") for p in data.get("data", []) if p.get("status", "").lower() == "granted"]
            return [p.lower() for p in (perms or []) if p]

    async def missing_permissions(self, access_token: str, required: List[str]) -> List[str]:
        """Check which of the required permissions are missing from the granted set.

        Normalizes legacy/business-prefixed names to official Instagram Graph names
        (e.g., instagram_business_basic -> instagram_basic) for compatibility.
        """
        def canonical(name: str) -> str:
            n = (name or "").lower()
            mapping = {
                # Map legacy/business-prefixed names to official names
                "instagram_business_basic": "instagram_basic",
                "instagram_business_manage_messages": "instagram_manage_messages",
                "instagram_business_manage_comments": "instagram_manage_comments",
                "instagram_business_content_publish": "instagram_content_publish",
            }
            return mapping.get(n, n)

        granted = await self.fetch_permissions(access_token)
        granted_set = {canonical(g) for g in (granted or [])}
        required_canon = [canonical(r) for r in (required or [])]
        missing = [r for r, rc in zip(required, required_canon) if rc not in granted_set]
        logging.debug(
            f"Permission check - Required(canon): {required_canon}, Granted(canon): {list(granted_set)}, Missing(original): {missing}"
        )
        return missing

    async def store_facebook_connection(self, user_email: str, access_token: str, fb_user_id: Optional[str] = None, fb_pages: Optional[list] = None):
        # fetch granted permissions and persist them with the token
        try:
            granted = await self.fetch_permissions(access_token)
        except Exception:
            granted = []

        # fetch ad accounts
        ad_accounts = []
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(
                    "https://graph.facebook.com/v22.0/me/adaccounts",
                    params={
                        "fields": "id,name,currency,account_status",
                        "access_token": access_token,
                    },
                    timeout=10.0,
                )
                r.raise_for_status()
                ad_accounts = r.json().get("data", [])
        except Exception:
            ad_accounts = []

        doc = await self.facebook_repo.create_or_update(
            user_email,
            access_token,
            fb_user_id=fb_user_id,
            fb_pages=fb_pages,
            granted_scopes=granted,
            ad_accounts=ad_accounts,
        )
        # mark user profile flag
        await self.user_repo.update_connection_flags(user_email, facebook=True)
        
        # Trigger Notification
        try:
             from application.services.notification_service import NotificationService
             from infrastructure.database.models.notification_model import NotificationType
             notif_service = NotificationService()
             await notif_service.create_and_send(
                 user_id=user_email,
                 type=NotificationType.SYSTEM,
                 title="Facebook Connected",
                 message="Your Facebook Ads account has been successfully connected.",
                 metadata={
                     "channel": "facebook",
                     "pages_count": len(fb_pages) if fb_pages else 0,
                     "ad_accounts_count": len(ad_accounts) if ad_accounts else 0,
                 }
             )
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")

        return doc

    async def fetch_ig_account_for_page(self, access_token: str, page_id: str) -> Optional[Dict[str, Any]]:
        # Try several possible fields (depends on Graph API version and app privileges)
        url = f"https://graph.facebook.com/v22.0/{page_id}"
        params = {"fields": "instagram_business_account", "access_token": access_token}
        async with httpx.AsyncClient() as client:
            try:
                r = await client.get(url, params=params, timeout=10.0)
                r.raise_for_status()
                data = r.json()
                for key in ("connected_instagram_account", "connected_instagram_business_account", "instagram_business_account"):
                    val = data.get(key)
                    if val:
                        return val
                return None
            except httpx.HTTPStatusError as e:
                # Log the actual error response from Facebook
                error_body = e.response.text
                try:
                    error_json = e.response.json()
                    error_code = error_json.get('error', {}).get('code')
                    error_msg = error_json.get('error', {}).get('message', '')
                    logging.error(f"Facebook Graph API error for page {page_id}: Code={error_code}, Message={error_msg}")
                    # Check if it's a permission error or invalid ID
                    if error_code in (10, 200, 190):  # Permission/auth errors
                        logging.warning(f"Permission issue accessing Instagram for page {page_id}")
                    elif error_code in (803, 100):  # Invalid ID or parameter errors
                        logging.warning(f"Invalid page ID or access token issue for page {page_id}")
                except Exception:
                    logging.error(f"Facebook Graph API error for page {page_id}: {error_body}")
                # Return None instead of raising - page might not have Instagram
                return None

    async def fetch_pages_with_ig(self, access_token: str) -> List[Dict[str, Any]]:
        """Return pages with an added `has_instagram` boolean and optional `instagram` details when linked."""
        pages = await self.fetch_fb_pages(access_token)
        results = []
        for p in pages:
            page_id = p.get("id")
            page_token = p.get("access_token")
            has_ig = False
            ig_info = None
            if page_token and page_id:
                try:
                    ig = await self.fetch_ig_account_for_page(page_token, page_id)
                    if ig:
                        has_ig = True
                        ig_id = ig.get("id") if isinstance(ig, dict) else None
                        if ig_id:
                            try:
                                ig_details = await self.fetch_ig_details(page_token, ig_id)
                                ig_info = ig_details
                            except Exception:
                                ig_info = ig
                except Exception:
                    has_ig = False
            results.append({"id": p.get("id"), "name": p.get("name"), "has_instagram": has_ig, "instagram": ig_info})
        return results

    async def fetch_ig_details(self, access_token: str, ig_business_id: str) -> Optional[Dict[str, Any]]:
        # fetch username, profile_picture_url, account_type
        url = f"https://graph.facebook.com/v22.0/{ig_business_id}"
        params = {"fields": "username,profile_picture_url,account_type", "access_token": access_token}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            return r.json()

    async def store_instagram_connection(self, user_email: str, ig_business_id: str, username: Optional[str] = None, account_type: Optional[str] = None, linked_fb_page_id: Optional[str] = None, profile_picture_url: Optional[str] = None, page_access_token: Optional[str] = None, user_access_token: Optional[str] = None):
        # encrypt tokens if provided
        enc_page_token = self.encryption_service.encrypt(page_access_token) if page_access_token else None
        enc_user_token = self.encryption_service.encrypt(user_access_token) if user_access_token else None
        
        # set profile_picture_url if available
        doc = await self.instagram_repo.find_by_user_id(user_email)
        if not doc:
            return await self.instagram_repo.create_or_update(
                user_email, 
                ig_business_id=ig_business_id, 
                username=username, 
                account_type=account_type, 
                linked_fb_page_id=linked_fb_page_id,
                page_access_token=enc_page_token,
                user_access_token=enc_user_token,
                profile_picture_url=profile_picture_url
            )
        
        # update fields including profile_picture_url and tokens
        if ig_business_id:
            doc.ig_business_id = ig_business_id
        if username:
            doc.username = username
        if account_type:
            doc.account_type = account_type
        if linked_fb_page_id:
            doc.linked_fb_page_id = linked_fb_page_id
        if profile_picture_url:
            doc.profile_picture_url = profile_picture_url
        if enc_page_token:
            doc.page_access_token = enc_page_token
        if enc_user_token:
            doc.user_access_token = enc_user_token
            
        doc.token_valid = True
        doc.updated_at = __import__('datetime').datetime.utcnow()
        await doc.save()
        # mark user profile flag
        await self.user_repo.update_connection_flags(user_email, instagram=True)
        
        # Trigger Notification
        try:
             from application.services.notification_service import NotificationService
             from infrastructure.database.models.notification_model import NotificationType
             notif_service = NotificationService()
             await notif_service.create_and_send(
                 user_id=user_email,
                 type=NotificationType.SYSTEM,
                 title="Instagram Connected",
                 message=f"Instagram account '{username or 'unknown'}' linked successfully.",
                 metadata={"channel": "instagram", "username": username}
             )
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            
        return doc

    async def store_google_business(self, user_email: str, business_name: str, address: str, latitude: float, longitude: float, place_id: str):
        doc = await self.google_repo.create_or_update(user_email, business_name=business_name, address=address, latitude=latitude, longitude=longitude, place_id=place_id)
        # mark user profile flag
        await self.user_repo.update_connection_flags(user_email, google_maps=True)
        
        # Trigger Notification
        try:
             from application.services.notification_service import NotificationService
             from infrastructure.database.models.notification_model import NotificationType
             notif_service = NotificationService()
             await notif_service.create_and_send(
                 user_id=user_email,
                 type=NotificationType.SYSTEM,
                 title="Google Business Connected",
                 message=f"Location '{business_name}' has been linked.",
                 metadata={"channel": "google", "business_name": business_name}
             )
        except Exception as e:
            logging.error(f"Failed to send notification: {e}")
            
        return doc
        
    async def sync_business_setup_to_flags(self, user_email: str):
        """Ensure user flags match Business Setup status"""
        from infrastructure.repositories.business_repository import BusinessRepository
        business_repo = BusinessRepository()
        business = await business_repo.get_by_user_id(user_email)
        if business and business.google_place_id:
            await self.user_repo.update_connection_flags(user_email, google_maps=True)

    # Retrieval helpers
    async def get_facebook_connection(self, user_email: str) -> Optional[dict]:
        fb = await self.facebook_repo.find_by_user_id(user_email)
        if not fb:
            return None
        return {
            "user_id": fb.user_id,
            "access_token": fb.access_token,
            "fb_user_id": fb.fb_user_id,
            "fb_pages": [p.dict() for p in fb.fb_pages] if getattr(fb, 'fb_pages', None) else []
        }

    async def get_instagram_connection(self, user_email: str) -> Optional[dict]:
        ig = await self.instagram_repo.find_by_user_id(user_email)
        if not ig:
            return None
        return {
            "user_id": ig.user_id,
            "ig_business_id": ig.ig_business_id,
            "username": ig.username,
            "profile_picture_url": getattr(ig, 'profile_picture_url', None),
            "account_type": ig.account_type,
            "linked_fb_page_id": ig.linked_fb_page_id,
        }

    async def get_google_business_connection(self, user_email: str) -> Optional[dict]:
        g = await self.google_repo.find_by_user_id(user_email)
        if not g:
            return None
        return {
            "user_id": g.user_id,
            "business_name": g.business_name,
            "address": g.business_address,
            "latitude": g.latitude,
            "longitude": g.longitude,
            "place_id": g.google_place_id,
        }

    # Instagram OAuth methods (separate from Facebook)
    def build_instagram_oauth_url(self, user_email: str, state: Optional[str] = None) -> str:
        """Build Instagram OAuth URL using Instagram app credentials"""
        raw = getattr(settings, "INSTAGRAM_OAUTH_SCOPES", None)
        if raw:
            if isinstance(raw, str):
                scopes = [s.strip() for s in raw.split(",") if s.strip()]
            elif isinstance(raw, (list, tuple)):
                scopes = list(raw)
            else:
                scopes = ["instagram_business_basic"]
        else:
            scopes = ["instagram_business_basic"]
        
        logging.info(f"Building Instagram OAuth URL for {user_email} with scopes: {','.join(scopes)}")
        
        from urllib.parse import quote
        params = {
            "client_id": settings.INSTAGRAM_APP_ID,
            "redirect_uri": f"{settings.BACKEND_URL}/api/profile/onboarding/instagram/callback",
            "scope": ",".join(scopes),
            "response_type": "code"
        }
        if state:
            params["state"] = state
        
        qs = "&".join([f"{k}={quote(v) if isinstance(v, str) else v}" for k, v in params.items()])
        return f"https://www.facebook.com/v22.0/dialog/oauth?{qs}"

    async def exchange_instagram_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange Instagram OAuth code for access token"""
        url = "https://graph.facebook.com/v22.0/oauth/access_token"
        params = {
            "client_id": settings.INSTAGRAM_APP_ID,
            "redirect_uri": f"{settings.BACKEND_URL}/api/profile/onboarding/instagram/callback",
            "client_secret": settings.INSTAGRAM_APP_SECRET,
            "code": code,
        }
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            access_token = data.get("access_token")
            if not access_token:
                raise ValueError("No access token in Instagram OAuth response")
            return data
