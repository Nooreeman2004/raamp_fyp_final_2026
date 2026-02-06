"""
Security Settings Repository
Handles CRUD operations for security_settings collection
"""
from typing import Optional
from datetime import datetime
from infrastructure.database.models.security_settings_model import SecuritySettingsModel


class SecuritySettingsRepository:
    """Repository for security settings operations"""
    
    async def get_by_user_id(self, user_id: str) -> Optional[SecuritySettingsModel]:
        """Get security settings for a user"""
        return await SecuritySettingsModel.find_one(
            SecuritySettingsModel.user_id == user_id
        )
    
    async def create_or_update(
        self,
        user_id: str,
        two_factor_enabled: bool,
        login_alerts: bool,
        session_timeout_minutes: int,
        trusted_devices_only: bool,
        password_change_required: bool
    ) -> SecuritySettingsModel:
        """Create or update security settings for a user"""
        existing = await self.get_by_user_id(user_id)
        
        if existing:
            # Update existing settings
            existing.two_factor_enabled = two_factor_enabled
            existing.login_alerts = login_alerts
            existing.session_timeout_minutes = session_timeout_minutes
            existing.trusted_devices_only = trusted_devices_only
            existing.password_change_required = password_change_required
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return existing
        else:
            # Create new settings
            settings = SecuritySettingsModel(
                user_id=user_id,
                two_factor_enabled=two_factor_enabled,
                login_alerts=login_alerts,
                session_timeout_minutes=session_timeout_minutes,
                trusted_devices_only=trusted_devices_only,
                password_change_required=password_change_required
            )
            await settings.insert()
            return settings
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete security settings for a user"""
        existing = await self.get_by_user_id(user_id)
        if existing:
            await existing.delete()
            return True
        return False
