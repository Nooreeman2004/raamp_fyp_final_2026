# FastAPI Application Entry Point
# Load environment variables FIRST before any other imports
import os
from pathlib import Path
from dotenv import load_dotenv

# Pin .env to this file's directory so it loads correctly regardless of the CWD
# (i.e. starting uvicorn from the repo root, parent folder, etc. all work)
_ENV_FILE = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=True)

# --- Startup sanity check (safe to leave in — prints only to server console) ---
_token_loaded = bool(os.getenv("META_WEBHOOK_VERIFY_TOKEN"))
_secret_loaded = bool(os.getenv("FACEBOOK_APP_SECRET"))
print(f"[ENV CHECK] META_WEBHOOK_VERIFY_TOKEN loaded: {_token_loaded}")
print(f"[ENV CHECK] FACEBOOK_APP_SECRET loaded: {_secret_loaded}")
print(f"[ENV CHECK] .env path used: {_ENV_FILE} (exists={_ENV_FILE.exists()})")
if not _token_loaded or not _secret_loaded:
    print("[ENV CHECK] ⚠️  WARNING: One or more required webhook env vars are missing. Webhooks will fail.")
    print(f"[ENV CHECK]    Hint: Make sure {_ENV_FILE} exists and contains META_WEBHOOK_VERIFY_TOKEN and FACEBOOK_APP_SECRET.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging
logger = logging.getLogger(__name__)

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import traceback
from datetime import datetime

from slowapi.errors import RateLimitExceeded
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from presentation.routers import auth_router
from infrastructure.database.database import connect_to_mongo, close_mongo_connection, init_db
from config import Config
from application.services.firebase_service import firebase_service
from application.services.cleanup_service import cleanup_service
from application.services.instagram_scheduler_service import process_scheduled_posts, InstagramSchedulerService
from application.services.token_expiry_monitor_service import check_token_expiry
from application.services.job_health_monitor_service import check_scheduler_health, cleanup_job_logs
from application.services.trend_detection_service import TrendDetectionService
from application.services.instagram_roi_service import scheduled_roi_refresh
from application.services.caption_roi_join_service import backfill_caption_log_engagement_rates
from application.services.geo_intent_notification_scheduler import send_daily_best_posting_time_notifications
from tasks.trend_retry_worker import process_due_trend_retries
from tasks.trend_expiry_worker import expire_old_trend_detections
from tasks.auto_reply_worker import process_due_auto_replies
from tasks.auto_reply_draft_expiry_worker import expire_auto_reply_drafts
from tasks.ab_test_schedule_worker import process_ab_test_schedule_transitions
from infrastructure.database.models.instagram_connection_model import InstagramConnectionModel

# External service instances for scheduling
trend_detection_service = TrendDetectionService()

async def run_trend_detection():
    """Wrapper function for scheduled trend detection"""
    await trend_detection_service.run_detection_for_all_users()


async def run_trend_expiry():
    """Wrapper function to expire old detections (keeps dashboards clean)."""
    await expire_old_trend_detections(ttl_hours=72)

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
    # Prevent httpx from logging full request URLs (can leak API keys in query params).
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.info("Starting RAAMP API...")
    await connect_to_mongo()
    await init_db()
    firebase_service.initialize()  # Initialize Firebase
    logging.info("MongoDB connected and initialized")

    # Instagram integration observability (per-user connection model).
    # This does not validate every token at startup (would be expensive), but it surfaces system state.
    try:
        total_ig = await InstagramConnectionModel.find_all().count()
        invalid_ig = await InstagramConnectionModel.find(InstagramConnectionModel.token_valid == False).count()  # noqa: E712
        logging.info("Instagram connections: total=%d token_valid_false=%d", total_ig, invalid_ig)
    except Exception as e:
        logging.warning("Instagram connection status check failed (non-fatal): %s", str(e))

    # Validate Geo-Intent Marketing Engine environment variables
    try:
        Config.validate_geo_intent_keys()
        logging.info("Geo-Intent engine env keys validated")
    except RuntimeError as geo_err:
        logging.warning("Geo-Intent engine startup warning: %s", geo_err)

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

    # Trend retry queue worker (every minute)
    scheduler.add_job(
        process_due_trend_retries,
        CronTrigger(minute='*'),
        id='process_due_trend_retries',
        name='Process due trend retry jobs',
        replace_existing=True
    )
    logging.info("Trend retry worker configured (every minute)")

    # Auto reply worker (every minute)
    scheduler.add_job(
        process_due_auto_replies,
        CronTrigger(minute='*'),
        id='process_due_auto_replies',
        name='Process due auto reply events',
        replace_existing=True
    )
    logging.info("Auto reply worker configured (every minute)")

    # Auto reply draft expiry (every hour)
    scheduler.add_job(
        expire_auto_reply_drafts,
        CronTrigger(minute=0),  # hourly at :00
        id='expire_auto_reply_drafts',
        name='Expire auto reply drafts and notify users',
        replace_existing=True
    )
    logging.info("Auto reply draft expiry configured (hourly)")

    # A/B optimizer schedule transition worker (every minute)
    scheduler.add_job(
        process_ab_test_schedule_transitions,
        CronTrigger(minute='*'),
        id='process_ab_test_schedule_transitions',
        name='A/B optimizer: status transitions + notifications',
        replace_existing=True
    )
    logging.info("A/B optimizer schedule worker configured (every minute)")

    # Expire old trend detections (every 10 minutes)
    scheduler.add_job(
        run_trend_expiry,
        CronTrigger(minute='*/10'),
        id='expire_old_trend_detections',
        name='Expire old trend detections (72h TTL)',
        replace_existing=True
    )
    logging.info("Trend expiry worker configured (every 10 minutes)")

    # Start ROI refresh scheduler (every 6 hours)
    scheduler.add_job(
        scheduled_roi_refresh,
        CronTrigger(hour='*/6'),  # Every 6 hours
        id='scheduled_roi_refresh',
        name='Refresh Instagram ROI metrics',
        replace_existing=True
    )
    logging.info("ROI refresh scheduler configured (every 6 hours)")

    # Backfill caption_logs.engagement_rate from ROI (every 6 hours, offset)
    # Runs after ROI refresh so freshly fetched metrics can label captions for ML training.
    scheduler.add_job(
        backfill_caption_log_engagement_rates,
        CronTrigger(hour='*/6', minute=15),  # Every 6 hours at :15
        id='backfill_caption_log_engagement_rates',
        name='Backfill caption engagement_rate from Instagram ROI',
        replace_existing=True
    )
    logging.info("Caption ROI join scheduler configured (every 6 hours at :15)")

    # Geo-Intent daily best time to post (daily at 9:05 UTC)
    scheduler.add_job(
        send_daily_best_posting_time_notifications,
        CronTrigger(hour=9, minute=5),
        id="geo_intent_daily_best_time",
        name="Geo-Intent: daily best time to post notification",
        replace_existing=True,
    )
    logging.info("Geo-Intent daily best-time notification configured (daily at 9:05 UTC)")

    # Startup RAG Health Check (validates Pinecone and OpenAI)
    try:
        from presentation.routers.chatbot_router import get_generator
        generator = get_generator()
        rag_health = generator.health_check()
        if rag_health.get("status") == "healthy":
            logging.info("RAG Engine (Pinecone + LangChain) initialized successfully")
        else:
            logging.warning("RAG Engine started with issues: %s", rag_health.get("error"))
    except Exception as rag_err:
        logging.error("CRITICAL: RAG Engine failed to initialize: %s", str(rag_err))
        # We don't exit(1) here to allow the rest of the app to function if RAG is optional,
        # but since we moved imports to top, it will fail earlier anyway if deps are missing.

    # Background Pinecone Warm-up (non-blocking)
    async def warmup_rag():
        try:
            await asyncio.sleep(5) # Wait for server to be fully up
            from presentation.routers.chatbot_router import get_generator
            gen = get_generator()
            # Deeper warm-up by actually querying
            gen.retriever.retrieve("warmup search query", n_results=1)
            logging.info("RAG Engine background warm-up complete")
        except Exception as e:
            logging.warning("RAG Engine warm-up failed: %s", str(e))

    asyncio.create_task(warmup_rag())

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

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Log all unhandled exceptions to a file for analysis"""
    from datetime import datetime
    import traceback
    import uuid

    # We use a local logger reference to avoid potential NameErrors during early startup/shutdown
    handler_logger = logging.getLogger("raamp.exception_handler")

    request_id = str(uuid.uuid4())
    tb = traceback.format_exc()
    try:
        with open("raamp_error.log", "a") as f:
            f.write(f"\n--- {datetime.utcnow()} --- request_id={request_id}\n")
            f.write(f"URL: {request.url}\n")
            f.write(tb)
    except Exception:
        pass

    handler_logger.error(
        "Unhandled Exception [%s]: %s",
        request_id,
        str(exc),
        exc_info=True,
    )

    # Never expose raw exception strings to clients in production (can leak paths, SQL, secrets).
    if Config.is_production():
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal Server Error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": request_id,
            },
        )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal Server Error",
            "message": str(exc),
            "request_id": request_id,
        },
    )

# CORS Configuration (extend via CORS_ALLOW_ORIGINS in .env — comma-separated origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.cors_allow_origins_list(),
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
from presentation.routers import content_generation_router
from presentation.routers import complaints_router
from presentation.routers import media_generation_router
# New routers for settings, billing, and geo-intent
from presentation.routers import settings_router
from presentation.routers import billing_router
from presentation.routers import notification_router
# New routers for enhanced Instagram functionality
from presentation.routers import social_status_router
from presentation.routers import assets_router
from presentation.routers import posting_logs_router
from presentation.routers import variant_recommendation_router
from presentation.routers import unified_posting_router
from presentation.routers import campaign_launch_router
from presentation.routers import campaign_drafts_router
from presentation.routers import campaign_planner_router
from presentation.routers import instagram_roi_router
# Trend Signal router for Google Trends integration
from presentation.routers import trend_signal_router
from presentation.routers import arbitrage_router
from presentation.routers import watchlist_router
from presentation.routers import stripe_router
# Geo-Intent Marketing Engine router (real-world signals, replaces simulation)
from presentation.routers import geo_intent_engine_router
from presentation.routers import dashboard_analytics_router
from presentation.routers import dashboard_posting_recommendations_router
from presentation.routers import ml_router
from presentation.routers import activity_router
from presentation.routers.meta_ads_router import router as meta_ads_router
from presentation.routers import meta_webhook_router
from presentation.routers import auto_reply_router
from presentation.routers import comment_analysis_router
from presentation.routers import social_escalation_router
from fastapi import Depends
from presentation.routers.auth_router import get_current_user_email
from application.services.onboarding_service import OnboardingService
from presentation.routers import legacy_assets_router
from presentation.routers import chatbot_router
from presentation.routers import ab_optimizer_router
# Instantiate a shared onboarding service for top-level routes
onboarding_service = OnboardingService()

app.include_router(auth_router.router, prefix="/api")
app.include_router(legacy_assets_router.router)
app.include_router(business_domain_router.router, prefix="/api")
app.include_router(logout_router.router, prefix="/api")
app.include_router(admin_router.router, prefix="/api")
app.include_router(onboarding_router.router)
app.include_router(profile_connections_router.router)
app.include_router(maps_router.router)
app.include_router(maps_public_router.router)
app.include_router(instagram_router.router)
app.include_router(instagram_posting_router.router)
app.include_router(instagram_roi_router.router)
app.include_router(instagram_scheduler_router.router)
app.include_router(facebook_posting_router.router)
app.include_router(brand_alignment_router.router)
app.include_router(hyperlocal_setup_router.router)
app.include_router(consultation_router.router)

# Chatbot router (RAG/langchain)
app.include_router(chatbot_router.router, prefix="/api")
logging.info("Chatbot router loaded")

app.include_router(ab_optimizer_router.router)
app.include_router(content_generation_router.router)
app.include_router(media_generation_router.router)  # Reel & Video generation
app.include_router(complaints_router.router)
# New routers for settings, billing, and geo-intent
app.include_router(settings_router.router)
app.include_router(billing_router.router)
app.include_router(notification_router.router)
# New routers for enhanced Instagram functionality
app.include_router(social_status_router.router)
app.include_router(assets_router.router)
app.include_router(posting_logs_router.router)
app.include_router(variant_recommendation_router.router)
app.include_router(unified_posting_router.router)
app.include_router(campaign_launch_router.router)
app.include_router(campaign_drafts_router.router)
app.include_router(campaign_planner_router.router)
# Trend Signal router for Google Trends integration
app.include_router(trend_signal_router.router, prefix="/api")
app.include_router(arbitrage_router.router, prefix="/api")
app.include_router(watchlist_router.router, prefix="/api")
app.include_router(stripe_router.router, prefix="/api")
# Geo-Intent Marketing Engine — real-world signals at /api/v1/geo
app.include_router(geo_intent_engine_router.router)
# Dashboard Analytics — Home Dashboard Real-time Support
app.include_router(dashboard_analytics_router.router)
app.include_router(dashboard_posting_recommendations_router.router)
app.include_router(activity_router.router)
app.include_router(ml_router.router)  # ML Caption Intelligence endpoints
app.include_router(meta_ads_router)
app.include_router(meta_webhook_router.router)
app.include_router(auto_reply_router.router)
logger.info("🔌 Including Comment Analysis Router...")
app.include_router(comment_analysis_router.router)
app.include_router(social_escalation_router.router)

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
