# FastAPI Application Entry Point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from presentation.routers import auth_router
from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db
from application.services.firebase_service import firebase_service
from application.services.cleanup_service import cleanup_service

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown events"""
    # Startup
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting RAAMP API...")
    await connect_to_mongo()
    await init_db()
    firebase_service.initialize()  # Initialize Firebase
    logging.info("MongoDB connected and initialized")

    # Start OTP cleanup service
    cleanup_task = asyncio.create_task(cleanup_service.start_scheduled_cleanup())
    logging.info("OTP cleanup service started")
    
    yield
    
    # Shutdown
    cleanup_service.stop_scheduled_cleanup()
    logging.info("OTP cleanup service stopped")
    await close_mongo_connection()
    logging.info("Shutting down RAAMP API...")


# Create FastAPI app
app = FastAPI(
    title="RAAMP API",
    description="Backend API for RAAMP - Revolutionary AI-Powered Autonomous Marketing Platform",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:5173",
        "http://localhost:8080",
        "http://localhost:8081",  # Frontend dev server
        "http://localhost:8082",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8082",
        "http://[::1]:8080",  # IPv6 localhost
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include routers

from presentation.routers import business_domain_router
from presentation.routers import logout_router
from presentation.routers import onboarding_router
from presentation.routers import profile_connections_router
from presentation.routers import maps_router
from presentation.routers import maps_public_router
from presentation.routers import instagram_router
from presentation.routers import brand_alignment_router
from presentation.routers import hyperlocal_setup_router
from presentation.routers import consultation_router
from presentation.routers import admin_router
from presentation.routers import chatbot_router
from fastapi import Depends
from presentation.routers.auth_router import get_current_user_email
from application.services.onboarding_service import OnboardingService

# Instantiate a shared onboarding service for top-level routes
onboarding_service = OnboardingService()

app.include_router(auth_router.router, prefix="/api")
app.include_router(business_domain_router.router, prefix="/api")
app.include_router(logout_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(onboarding_router.router)
app.include_router(profile_connections_router.router)
app.include_router(maps_router.router)
app.include_router(maps_public_router.router)
app.include_router(instagram_router.router)
app.include_router(brand_alignment_router.router)
app.include_router(hyperlocal_setup_router.router)
app.include_router(consultation_router.router)
app.include_router(chatbot_router.router, prefix="/api")


@app.get("/profile/onboarding")
async def frontend_profile_onboarding(current_user_email: str = Depends(get_current_user_email)):
    """Return merged profile + social connections + location for frontend route `/profile/onboarding`"""
    # gather profile summary
    profile = await onboarding_service.user_repo.get_profile_summary(current_user_email)
    # gather connections
    fb = await onboarding_service.get_facebook_connection(current_user_email)
    ig = await onboarding_service.get_instagram_connection(current_user_email)
    google = await onboarding_service.get_google_business_connection(current_user_email)
    return {
        "profile": profile or {},
        "connections": {
            "facebook": fb or {},
            "instagram": ig or {},
            "google_business": google or {}
        }
    }


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "message": "RAAMP API is running",
        "version": "1.0.0",
        "database": "MongoDB Atlas"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
