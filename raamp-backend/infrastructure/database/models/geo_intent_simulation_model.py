"""
Geo Intent Simulation Model for MongoDB
Collection: geo_intent_simulations
Stores simulation results for analytics and caching
"""
from beanie import Document
from pydantic import Field
from typing import List
from datetime import datetime


class GeoIntentSimulationModel(Document):
    """Geo-intent simulation results stored in MongoDB"""
    
    # Request tracking
    request_id: str = Field(..., description="Unique request identifier")
    user_id: str = Field(..., description="Reference to the user who made the request")
    
    # Simulation results
    hot_regions: List[dict] = Field(..., description="List of hot regions generated")
    total_regions: int = Field(..., description="Number of regions in this simulation")
    
    # Metadata
    simulation_params: dict = Field(default_factory=dict, description="Parameters used for simulation")
    analysis_metadata: dict = Field(default_factory=dict, description="Additional analysis info")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "geo_intent_simulations"
        indexes = [
            "user_id",
            "request_id",
            "created_at",
        ]
