"""
Billing Profile Repository
Handles CRUD operations for billing_profiles collection
"""
from typing import Optional
from datetime import datetime
from infrastructure.database.models.billing_profile_model import BillingProfileModel


class BillingProfileRepository:
    """Repository for billing profile operations"""
    
    async def get_by_user_id(self, user_id: str) -> Optional[BillingProfileModel]:
        """Get billing profile for a user"""
        return await BillingProfileModel.find_one(
            BillingProfileModel.user_id == user_id
        )
    
    async def create_or_update(
        self,
        user_id: str,
        full_name: str,
        company_name: str,
        email: str,
        phone: str,
        address_line1: str,
        address_line2: str,
        city: str,
        state: str,
        postal_code: str,
        country: str,
        tax_id: str,
        payment_method_type: str,
        card_last_four: str,
        card_expiry_month: int,
        card_expiry_year: int
    ) -> BillingProfileModel:
        """Create or update billing profile for a user"""
        existing = await self.get_by_user_id(user_id)
        
        if existing:
            # Update existing profile
            existing.full_name = full_name
            existing.company_name = company_name
            existing.email = email
            existing.phone = phone
            existing.address_line1 = address_line1
            existing.address_line2 = address_line2
            existing.city = city
            existing.state = state
            existing.postal_code = postal_code
            existing.country = country
            existing.tax_id = tax_id
            existing.payment_method_type = payment_method_type
            existing.card_last_four = card_last_four
            existing.card_expiry_month = card_expiry_month
            existing.card_expiry_year = card_expiry_year
            existing.updated_at = datetime.utcnow()
            await existing.save()
            return existing
        else:
            # Create new profile
            profile = BillingProfileModel(
                user_id=user_id,
                full_name=full_name,
                company_name=company_name,
                email=email,
                phone=phone,
                address_line1=address_line1,
                address_line2=address_line2,
                city=city,
                state=state,
                postal_code=postal_code,
                country=country,
                tax_id=tax_id,
                payment_method_type=payment_method_type,
                card_last_four=card_last_four,
                card_expiry_month=card_expiry_month,
                card_expiry_year=card_expiry_year
            )
            await profile.insert()
            return profile
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """Delete billing profile for a user"""
        existing = await self.get_by_user_id(user_id)
        if existing:
            await existing.delete()
            return True
        return False
