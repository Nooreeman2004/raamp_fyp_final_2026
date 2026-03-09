# Domain Layer - Trend Detection Entities
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict


@dataclass
class TrendSpike:
    """Represents a detected spike in a trend"""
    keyword: str
    z_score: float
    current_value: float
    expected_value: float  # EWMA value
    timestamp: datetime
    niche: str
    location: str


@dataclass
class TrendDetectionConfig:
    """Configurable parameters for the detection engine"""
    rolling_window: int = 14  # Days
    threshold: float = 2.0     # Z-score threshold for spike detection
    alpha: float = 0.3         # EWMA smoothing factor (0 to 1)
    min_data_points: int = 5   # Minimum points required to run detection
