"""
Consultation Request Router - handles consultation booking requests
"""
from fastapi import APIRouter, HTTPException, status
from infrastructure.repositories.consultation_request_repository import ConsultationRequestRepository
from presentation.schemas.consultation_schema import ConsultationRequestSchema, ConsultationResponseSchema
from application.services.mailtrap_service import MailtrapService
from pymongo.errors import DuplicateKeyError
import logging
import smtplib

router = APIRouter(prefix="/api/consultation", tags=["Consultation"])


@router.post(
    "/submit",
    response_model=ConsultationResponseSchema,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Consultation request submitted successfully"},
        400: {"description": "Validation error"},
        409: {"description": "Email already used for consultation request"},
        500: {"description": "Server error"}
    }
)
async def submit_consultation_request(
    consultation: ConsultationRequestSchema
):
    """
    Submit a consultation booking request
    
    - **All fields are required**
    - Validates and sanitizes all inputs
    - Stores in MongoDB with unique email constraint
    - Sends confirmation email via Mailtrap
    - Rate limited to 5 requests per minute per IP
    """
    try:
        # Create repository instance
        repo = ConsultationRequestRepository()
        
        # Check if email already exists (before attempting insert)
        existing = await repo.find_by_email(consultation.business_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email has already been used to book a consultation. Our team will contact you soon."
            )
        
        # Insert into MongoDB
        try:
            await repo.create(
                first_name=consultation.first_name,
                last_name=consultation.last_name,
                business_email=consultation.business_email,
                company_name=consultation.company_name
            )
        except DuplicateKeyError as e:
            # Handle race condition where duplicate is inserted between check and insert
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This email has already been used to book a consultation. Our team will contact you soon."
            ) from e
        
        # Send confirmation email via Mailtrap
        try:
            mailtrap_service = MailtrapService()
            
            email_subject = "Thank You for Booking Your Consultation with RAAMP"
            email_body = f"""
Dear {consultation.first_name},

Thank you for booking a free consultation with RAAMP!

We've received your request and are excited to help revolutionize your marketing strategy with our AI-powered autonomous marketing platform.

Our team will review your information and reach out to you within 24-48 business hours to schedule your consultation.

In the meantime, if you have any questions, please don't hesitate to contact us.

Best regards,
The RAAMP Team

---
Company: {consultation.company_name}
Email: {consultation.business_email}
"""
            
            html_email = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #00b4d8, #0077b6); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; }}
        .highlight {{ color: #0077b6; font-weight: bold; }}
        .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 12px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Thank You for Booking Your Consultation!</h1>
        </div>
        <div class="content">
            <p>Dear <span class="highlight">{consultation.first_name}</span>,</p>
            
            <p>Thank you for booking a free consultation with <strong>RAAMP</strong>!</p>
            
            <p>We've received your request and are excited to help revolutionize your marketing strategy with our AI-powered autonomous marketing platform.</p>
            
            <p><strong>What happens next?</strong></p>
            <ul>
                <li>Our team will review your information</li>
                <li>We'll reach out within <span class="highlight">24-48 business hours</span></li>
                <li>We'll schedule a convenient time for your consultation</li>
            </ul>
            
            <p>In the meantime, if you have any questions, please don't hesitate to contact us.</p>
            
            <div class="footer">
                <p><strong>Your Details:</strong></p>
                <p>Company: {consultation.company_name}<br>
                Email: {consultation.business_email}</p>
                
                <p>Best regards,<br>
                <strong>The RAAMP Team</strong></p>
            </div>
        </div>
    </div>
</body>
</html>
"""
            
            await mailtrap_service.send_custom_email(
                to_email=consultation.business_email,
                to_name=f"{consultation.first_name} {consultation.last_name}",
                subject=email_subject,
                text_content=email_body,
                html_content=html_email
            )
            
            logging.info("Consultation confirmation email sent to %s", consultation.business_email)
            
        except (smtplib.SMTPException, ConnectionError, TimeoutError) as email_error:
            # Log email error but don't fail the request
            logging.error("Failed to send consultation confirmation email: %s", email_error)
            # Continue - data is already saved in DB
        
        return ConsultationResponseSchema()
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    
    except ValueError as e:
        # Validation errors from Pydantic validators
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    
    except Exception as e:
        logging.error("Error processing consultation request: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process consultation request. Please try again later."
        ) from e
