"""
Business Repository - handles database operations for businesses
"""
from infrastructure.database.models.business_model import BusinessModel, ToneOfVoiceProfileModel
from infrastructure.database.models.user_model import UserModel
from typing import Optional
from datetime import datetime


class BusinessRepository:
    """Repository for business/restaurant data"""
    
    async def get_by_user_id(self, user_id: str) -> Optional[BusinessModel]:
        """Get business by user ID"""
        return await BusinessModel.find_one(BusinessModel.user_id == user_id)
    
    async def create(self, business_data: dict) -> BusinessModel:
        """Create new business"""
        business = BusinessModel(**business_data)
        await business.insert()
        return business
    
    async def update_brand_alignment(
        self,
        user_id: str,
        brand_logo_url: str,
        primary_color: str,
        secondary_color: str,
        tagline: str,
        tone_of_voice: str,
        tone_profile: Optional[dict] = None,
        restaurant_theme: Optional[str] = None,
        brand_colors: Optional[list[str]] = None,
        palette_source: str = "custom"
    ) -> BusinessModel:
        """Update or create brand alignment settings"""
        business = await self.get_by_user_id(user_id)
        
        safe_brand_colors = brand_colors or []

        if business:
            # Update existing
            business.brand_logo_url = brand_logo_url
            business.primary_color = primary_color
            business.secondary_color = secondary_color
            business.tagline = tagline
            business.tone_of_voice = tone_of_voice
            business.tone_profile = ToneOfVoiceProfileModel(**tone_profile) if tone_profile else None
            business.restaurant_theme = restaurant_theme
            business.brand_colors = safe_brand_colors
            business.palette_source = palette_source
            business.updated_at = datetime.utcnow()
            await business.save()
        else:
            # Create new
            business = await self.create({
                "user_id": user_id,
                "brand_logo_url": brand_logo_url,
                "primary_color": primary_color,
                "secondary_color": secondary_color,
                "tagline": tagline,
                "tone_of_voice": tone_of_voice,
                "tone_profile": ToneOfVoiceProfileModel(**tone_profile) if tone_profile else None,
                "restaurant_theme": restaurant_theme,
                "brand_colors": safe_brand_colors,
                "palette_source": palette_source
            })
        
        return business
    
    async def update_hyperlocal_setup(
        self,
        user_id: str,
        business_name: str,
        business_type: str,
        latitude: float,
        longitude: float,
        place_id: Optional[str] = None,
        formatted_address: Optional[str] = None,
        website: Optional[str] = None,
        phone_number: Optional[str] = None,
        description: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None
    ) -> BusinessModel:
        """Update or create hyperlocal business setup"""
        business = await self.get_by_user_id(user_id)
        
        if business:
            # Update existing
            business.business_name = business_name
            business.business_type = business_type
            business.latitude = latitude
            business.longitude = longitude
            business.google_place_id = place_id
            business.business_address = formatted_address
            business.website = website
            business.phone_number = phone_number
            business.description = description
            business.city = city
            business.country = country
            business.updated_at = datetime.utcnow()
            await business.save()
        else:
            # Create new
            business = await self.create({
                "user_id": user_id,
                "business_name": business_name,
                "business_type": business_type,
                "latitude": latitude,
                "longitude": longitude,
                "google_place_id": place_id,
                "business_address": formatted_address,
                "website": website,
                "phone_number": phone_number,
                "description": description,
                "city": city,
                "country": country
            })
            
        # Sync with UserModel connection flag
        user = await UserModel.get(user_id)
        if user:
            user.google_maps_connected = True
            await user.save()
        
        return business
