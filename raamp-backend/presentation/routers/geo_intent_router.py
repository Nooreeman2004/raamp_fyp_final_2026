"""
Geo Intent Router - handles geo-intent simulation for hot regions/ad targeting
"""
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
import uuid
import random

from presentation.schemas.settings_schemas import (
    GeoIntentResponse,
    HotRegion,
    ErrorResponse
)
from presentation.routers.auth_router import get_current_user_email
from infrastructure.repositories.geo_intent_simulation_repository import GeoIntentSimulationRepository


router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# Sample data for randomization
REGION_NAMES = [
    "Downtown Core", "Financial District", "Tech Hub", "University District",
    "Shopping Mall Area", "Residential Zone A", "Business Park", "Entertainment District",
    "Airport Vicinity", "Convention Center", "Stadium District", "Waterfront",
    "Historic Quarter", "Medical District", "Industrial Park", "Suburban Center",
    "Transit Hub", "Nightlife District", "Restaurant Row", "Arts District"
]

DEMOGRAPHICS = [
    "Young Professionals (25-34)", "Families with Children", "Students",
    "Senior Citizens", "High-Income Earners", "Middle-Class Consumers",
    "Tech Workers", "Healthcare Workers", "Retail Workers", "Tourists",
    "Business Travelers", "Local Commuters", "Fitness Enthusiasts",
    "Food Enthusiasts", "Nightlife Seekers", "Shoppers"
]

PEAK_HOURS = [
    "6:00 AM - 9:00 AM", "9:00 AM - 12:00 PM", "12:00 PM - 2:00 PM",
    "2:00 PM - 5:00 PM", "5:00 PM - 8:00 PM", "8:00 PM - 11:00 PM"
]


def generate_random_coordinates():
    """Generate random lat/lng coordinates (simulating a major city area)"""
    # Base coordinates around a fictional city center
    base_lat = 40.7128 + random.uniform(-0.15, 0.15)  # NYC-like latitude
    base_lng = -74.0060 + random.uniform(-0.15, 0.15)  # NYC-like longitude
    return {
        "lat": round(base_lat, 6),
        "lng": round(base_lng, 6)
    }


def generate_hot_region() -> dict:
    """Generate a random hot region with realistic data"""
    heat_score = random.randint(30, 100)
    
    # Higher heat score = more predicted customers
    base_customers = heat_score * random.randint(50, 150)
    predicted_customers = int(base_customers * (1 + random.uniform(-0.2, 0.3)))
    
    # Select random peak hours (1-3 time slots)
    num_peak_hours = random.randint(1, 3)
    selected_peak_hours = random.sample(PEAK_HOURS, num_peak_hours)
    
    # Select random demographics (2-4 groups)
    num_demographics = random.randint(2, 4)
    selected_demographics = random.sample(DEMOGRAPHICS, num_demographics)
    
    return {
        "region_name": random.choice(REGION_NAMES),
        "coordinates": generate_random_coordinates(),
        "heat_score": heat_score,
        "predicted_high_intent_customers": predicted_customers,
        "peak_hours": sorted(selected_peak_hours),
        "dominant_demographics": selected_demographics
    }


@router.get(
    "/geo-intent",
    response_model=GeoIntentResponse,
    responses={500: {"model": ErrorResponse}}
)
async def get_geo_intent_simulation(
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get simulated geo-intent data for hot regions (ad targeting).
    
    This is a SIMULATED endpoint that generates:
    - Hot regions for ad targeting
    - Heat scores (0-100) indicating customer intent
    - Predicted high-intent customer counts
    - Peak activity hours
    - Dominant demographics per region
    
    Each call returns randomized data to simulate real-time analytics.
    Results are stored in the database for analytics purposes.
    
    No external APIs are used - pure simulation for demonstration.
    """
    try:
        # Generate unique request ID
        request_id = f"GEO-{uuid.uuid4().hex[:16].upper()}"
        timestamp = datetime.utcnow()
        
        # Generate random number of hot regions (5-12)
        num_regions = random.randint(5, 12)
        
        # Generate hot regions
        hot_regions = []
        used_names = set()
        
        for _ in range(num_regions):
            region = generate_hot_region()
            # Ensure unique region names
            while region["region_name"] in used_names:
                region["region_name"] = random.choice(REGION_NAMES)
            used_names.add(region["region_name"])
            hot_regions.append(region)
        
        # Sort by heat score (highest first)
        hot_regions.sort(key=lambda x: x["heat_score"], reverse=True)
        
        # Generate analysis metadata
        total_predicted_customers = sum(r["predicted_high_intent_customers"] for r in hot_regions)
        avg_heat_score = sum(r["heat_score"] for r in hot_regions) / len(hot_regions)
        
        analysis_metadata = {
            "analysis_version": "2.1.0",
            "data_freshness": "real-time (simulated)",
            "confidence_level": f"{random.randint(85, 98)}%",
            "total_predicted_customers": total_predicted_customers,
            "average_heat_score": round(avg_heat_score, 1),
            "top_region": hot_regions[0]["region_name"] if hot_regions else None,
            "coverage_area_km2": round(random.uniform(50, 200), 1),
            "last_updated": timestamp.isoformat(),
            "next_refresh": "Auto-refresh every 15 minutes (simulated)"
        }
        
        # Store simulation in database
        try:
            repo = GeoIntentSimulationRepository()
            await repo.create(
                request_id=request_id,
                user_id=current_user_email,
                hot_regions=hot_regions,
                total_regions=num_regions,
                simulation_params={
                    "num_regions_requested": num_regions,
                    "timestamp": timestamp.isoformat()
                },
                analysis_metadata=analysis_metadata
            )
        except Exception as db_error:
            # Log but don't fail the request if DB save fails
            print(f"Warning: Failed to save simulation to DB: {db_error}")
        
        # Convert to response model
        hot_region_models = [
            HotRegion(
                region_name=r["region_name"],
                coordinates=r["coordinates"],
                heat_score=r["heat_score"],
                predicted_high_intent_customers=r["predicted_high_intent_customers"],
                peak_hours=r["peak_hours"],
                dominant_demographics=r["dominant_demographics"]
            )
            for r in hot_regions
        ]
        
        return GeoIntentResponse(
            success=True,
            request_id=request_id,
            timestamp=timestamp.isoformat(),
            total_regions=num_regions,
            hot_regions=hot_region_models,
            analysis_metadata=analysis_metadata
        )
        
    except Exception as e:
        print(f"Error generating geo-intent simulation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate geo-intent simulation"
        ) from e


@router.get(
    "/geo-intent/history",
    responses={500: {"model": ErrorResponse}}
)
async def get_geo_intent_history(
    limit: int = 10,
    current_user_email: str = Depends(get_current_user_email)
):
    """
    Get recent geo-intent simulation history for the current user.
    
    Parameters:
    - limit: Maximum number of results (default: 10, max: 50)
    """
    try:
        # Cap limit at 50
        limit = min(limit, 50)
        
        repo = GeoIntentSimulationRepository()
        simulations = await repo.get_recent_by_user(current_user_email, limit=limit)
        
        return {
            "success": True,
            "count": len(simulations),
            "simulations": [
                {
                    "request_id": sim.request_id,
                    "total_regions": sim.total_regions,
                    "created_at": sim.created_at.isoformat(),
                    "analysis_metadata": sim.analysis_metadata
                }
                for sim in simulations
            ]
        }
        
    except Exception as e:
        print(f"Error fetching geo-intent history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch geo-intent history"
        ) from e
