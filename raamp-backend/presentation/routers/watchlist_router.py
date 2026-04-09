
# Presentation Layer - Trend Watchlist Router
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from infrastructure.database.models.trend_watchlist_model import TrendWatchlistModel
from presentation.routers.auth_router import get_current_user_email

router = APIRouter(prefix="/trends/watchlist", tags=["Trend Watchlist"])

class WatchlistAddRequest(BaseModel):
    keyword: str
    niche: Optional[str] = "marketing"
    location: Optional[str] = "US"
    alert_threshold: Optional[float] = 5.0
    profit_score_threshold: Optional[float] = 75.0
    alert_on_saturation_drop: Optional[bool] = False
    saturation_drop_threshold: Optional[float] = 10.0

class WatchlistResponse(BaseModel):
    id: str
    keyword: str
    niche: str
    location: str
    last_velocity: float
    last_saturation: float
    last_arbitrage_score: float
    last_profit_score: float
    is_active: bool
    created_at: datetime

@router.post("/", response_model=WatchlistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    request: WatchlistAddRequest,
    current_user_email: str = Depends(get_current_user_email)
):
    # Check if already exists
    exists = await TrendWatchlistModel.find_one({
        "user_email": current_user_email,
        "keyword": {"$regex": f"^{request.keyword}$", "$options": "i"}
    })
    
    if exists:
        if exists.is_active:
            raise HTTPException(status_code=400, detail="Trend already in your watchlist")
        else:
            exists.is_active = True
            exists.updated_at = datetime.utcnow()
            await exists.save()
            return exists

    # Seed snapshot metrics from the latest detection (best-effort)
    last_velocity = 0.0
    last_saturation = 0.0
    last_arbitrage = 0.0
    try:
        from infrastructure.database.models.trend_detection_model import TrendDetectionModel
        det = await TrendDetectionModel.find_one(
            {
                "user_id": current_user_email,
                "keyword": {"$regex": f"^{request.keyword}$", "$options": "i"},
            }
        ).sort("-detected_at")
        if det:
            last_velocity = float(getattr(det, "z_score", 0.0) or 0.0)
            last_saturation = float(getattr(det, "current_value", 0.0) or 0.0)
            last_arbitrage = round((last_velocity * 5.0) + (100.0 - (last_saturation or 50.0)) / 2.0, 2)
    except Exception:
        pass

    item = TrendWatchlistModel(
        user_email=current_user_email,
        keyword=request.keyword,
        niche=request.niche,
        location=request.location,
        velocity_threshold=request.alert_threshold,
        profit_score_threshold=request.profit_score_threshold,
        alert_on_saturation_drop=bool(request.alert_on_saturation_drop),
        saturation_drop_threshold=request.saturation_drop_threshold,
        last_velocity=last_velocity,
        last_saturation=last_saturation,
        last_arbitrage_score=last_arbitrage,
        last_profit_score=0.0,
        updated_at=datetime.utcnow(),
    )
    await item.insert()
    
    return WatchlistResponse(
        id=str(item.id),
        keyword=item.keyword,
        niche=item.niche,
        location=item.location,
        last_velocity=item.last_velocity,
        last_saturation=item.last_saturation,
        last_arbitrage_score=item.last_arbitrage_score,
        last_profit_score=getattr(item, "last_profit_score", 0.0),
        is_active=item.is_active,
        created_at=item.created_at
    )

@router.get("/", response_model=List[WatchlistResponse])
async def get_watchlist(current_user_email: str = Depends(get_current_user_email)):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"👁️ WATCHLIST REQUEST - User: {current_user_email}")
    items = await TrendWatchlistModel.find({"user_email": current_user_email, "is_active": True}).to_list()
    logger.info(f"👁️ WATCHLIST RESPONSE - Returned {len(items)} watchlist items for {current_user_email}")
    return [
        WatchlistResponse(
            id=str(item.id),
            keyword=item.keyword,
            niche=item.niche,
            location=item.location,
            last_velocity=item.last_velocity,
            last_saturation=item.last_saturation,
            last_arbitrage_score=item.last_arbitrage_score,
            last_profit_score=getattr(item, "last_profit_score", 0.0),
            is_active=item.is_active,
            created_at=item.created_at
        ) for item in items
    ]

@router.delete("/{keyword}")
async def remove_from_watchlist(
    keyword: str,
    current_user_email: str = Depends(get_current_user_email)
):
    item = await TrendWatchlistModel.find_one({
        "user_email": current_user_email, 
        "keyword": {"$regex": f"^{keyword}$", "$options": "i"}
    })
    if not item:
        raise HTTPException(status_code=404, detail="Trend not found in watchlist")
    
    item.is_active = False
    await item.save()
    return {"message": f"Successfully removed {keyword} from watchlist"}
