# FastAPI Application Entry Point
# Load environment variables FIRST before any other imports
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from presentation.routers import auth_router
from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db
from application.services.firebase_service import firebase_service
from application.services.cleanup_service import cleanup_service
from application.services.instagram_scheduler_service import process_scheduled_posts, InstagramSchedulerService
from application.services.token_expiry_monitor_service import check_token_expiry
from application.services.job_health_monitor_service import check_scheduler_health, cleanup_job_logs
from application.services.trend_detection_service import TrendDetectionService

# External service instances for scheduling
trend_detection_service = TrendDetectionService()

async def run_trend_detection():
    """Wrapper function for scheduled trend detection"""
    await trend_detection_service.run_detection_for_all_users()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize scheduler
scheduler = AsyncIOScheduler()
scheduler_service = InstagramSchedulerService()


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
    
    # Start Instagram post scheduler (every minute)
    scheduler.add_job(
        process_scheduled_posts,
        CronTrigger(minute='*'),  # Every minute
        id='process_scheduled_posts',
        name='Process scheduled Instagram posts',
        replace_existing=True
    )
    logging.info("Instagram post scheduler configured (every minute)")
    
    # Start 10-minute reminder scheduler (every minute)
    scheduler.add_job(
        scheduler_service.send_10min_reminders,
        CronTrigger(minute='*'),  # Every minute
        id='send_10min_reminders',
        name='Send 10-minute reminders for scheduled posts',
        replace_existing=True
    )
    logging.info("10-minute reminder scheduler configured (every minute)")
    
    # Start token expiry monitoring (daily at 9 AM)
    scheduler.add_job(
        check_token_expiry,
        CronTrigger(hour=9, minute=0),  # Daily at 9 AM
        id='check_token_expiry',
        name='Check OAuth token expiry',
        replace_existing=True
    )
    logging.info("Token expiry monitoring configured (daily at 9 AM)")
    
    # Start job health monitoring (every 5 minutes)
    scheduler.add_job(
        check_scheduler_health,
        CronTrigger(minute='*/5'),  # Every 5 minutes
        id='check_scheduler_health',
        name='Monitor job health',
        replace_existing=True
    )
    logging.info("Job health monitoring configured (every 5 minutes)")
    
    # Start job log cleanup (daily at 3 AM)
    scheduler.add_job(
        cleanup_job_logs,
        CronTrigger(hour=3, minute=0),  # Daily at 3 AM
        id='cleanup_job_logs',
        name='Cleanup old job execution logs',
        replace_existing=True
    )
    logging.info("Job log cleanup configured (daily at 3 AM)")
    
    # Start Trend Detection Engine (every 30 minutes)
    scheduler.add_job(
        run_trend_detection,
        CronTrigger(minute='*/30'),  # Every 30 minutes
        id='run_trend_detection',
        name='Run emerging trend detection for all users',
        replace_existing=True
    )
    logging.info("Trend detection engine configured (every 30 minutes)")
    
    # Start the scheduler
    scheduler.start()
    logging.info("APScheduler started successfully")
    
    yield
    
    # Shutdown
    scheduler.shutdown(wait=False)
    logging.info("APScheduler stopped")
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
        "http://192.168.100.31:8080",  # Local LAN frontend
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
from presentation.routers import instagram_posting_router
from presentation.routers import instagram_scheduler_router
from presentation.routers import facebook_posting_router
from presentation.routers import brand_alignment_router
from presentation.routers import hyperlocal_setup_router
from presentation.routers import consultation_router
from presentation.routers import admin_router
from presentation.routers import chatbot_router
from presentation.routers import content_generation_router
from presentation.routers import complaints_router
from presentation.routers import media_generation_router
# New routers for settings, billing, and geo-intent
from presentation.routers import settings_router
from presentation.routers import billing_router
from presentation.routers import geo_intent_router
from presentation.routers import notification_router
# New routers for enhanced Instagram functionality
from presentation.routers import social_status_router
from presentation.routers import assets_router
from presentation.routers import posting_logs_router
from presentation.routers import variant_recommendation_router
from presentation.routers import unified_posting_router
# Trend Signal router for Google Trends integration
from presentation.routers import trend_signal_router
from presentation.routers import arbitrage_router
from presentation.routers import watchlist_router
from presentation.routers import stripe_router
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
app.include_router(instagram_posting_router.router)
app.include_router(instagram_scheduler_router.router)
app.include_router(facebook_posting_router.router)
app.include_router(brand_alignment_router.router)
app.include_router(hyperlocal_setup_router.router)
app.include_router(consultation_router.router)
app.include_router(chatbot_router.router, prefix="/api")
app.include_router(content_generation_router.router)
app.include_router(media_generation_router.router)  # Reel & Video generation
app.include_router(complaints_router.router)
# New routers for settings, billing, and geo-intent
app.include_router(settings_router.router)
app.include_router(billing_router.router)
app.include_router(geo_intent_router.router)
app.include_router(notification_router.router)
# New routers for enhanced Instagram functionality
app.include_router(social_status_router.router)
app.include_router(assets_router.router)
app.include_router(posting_logs_router.router)
app.include_router(variant_recommendation_router.router)
app.include_router(unified_posting_router.router)
# Trend Signal router for Google Trends integration
app.include_router(trend_signal_router.router, prefix="/api")
app.include_router(arbitrage_router.router, prefix="/api")
app.include_router(watchlist_router.router, prefix="/api")
app.include_router(stripe_router.router, prefix="/api")

# Mount static files for uploaded content
os.makedirs("uploaded_files", exist_ok=True)
app.mount("/api/static", StaticFiles(directory="uploaded_files"), name="static")

# Mount static files for AI-generated images
os.makedirs("generated_images", exist_ok=True)

# Mount static files for AI-generated videos and reels
os.makedirs("generated_videos", exist_ok=True)
app.mount("/api/videos", StaticFiles(directory="generated_videos"), name="videos")
os.makedirs("generated_reels", exist_ok=True)
app.mount("/api/reels", StaticFiles(directory="generated_reels"), name="reels")
app.mount("/api/generated", StaticFiles(directory="generated_images"), name="generated")


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
