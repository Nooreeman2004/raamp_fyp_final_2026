"""
Consultation Request Repository
"""
from infrastructure.database.models.consultation_request_model import ConsultationRequestModel
from typing import Optional
from pymongo.errors import DuplicateKeyError


class ConsultationRequestRepository:
    """Repository for consultation request data"""
    
    async def create(self, first_name: str, last_name: str, business_email: str, company_name: str) -> ConsultationRequestModel:
        """
        Create new consultation request
        
        Raises:
            DuplicateKeyError: If business_email already exists
        """
        consultation = ConsultationRequestModel(
            first_name=first_name,
            last_name=last_name,
            business_email=business_email,
            company_name=company_name
        )
        
        try:
            await consultation.insert()
            return consultation
        except DuplicateKeyError as e:
            raise DuplicateKeyError("This email has already been used to book a consultation") from e
    
    async def find_by_email(self, business_email: str) -> Optional[ConsultationRequestModel]:
        """Find consultation request by email"""
        return await ConsultationRequestModel.find_one(
            ConsultationRequestModel.business_email == business_email.lower()
        )
    
    async def count_by_email(self, business_email: str) -> int:
        """Count consultation requests by email"""
        return await ConsultationRequestModel.find(
            ConsultationRequestModel.business_email == business_email.lower()
        ).count()
