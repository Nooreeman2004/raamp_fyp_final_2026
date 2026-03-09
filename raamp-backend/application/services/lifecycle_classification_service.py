
# Application Layer - Lifecycle Classification Service
import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)


class LifecycleClassificationService:
    """
    Service for classifying trends into lifecycle stages:
    - Emerging: Low saturation, positive acceleration, low baseline
    - Breakout: High Z-score, strong short-term slope, low/medium saturation
    - Mainstream: High volume, flattening growth, moderate saturation
    - Saturated: High saturation, high ad density, slowing growth
    - Declining: Negative slope, falling Z-score
    """

    def classify_lifecycle(
        self,
        z_score: float,
        short_term_slope: float,  # 7-day slope
        long_term_slope: float,   # 30-day slope
        acceleration: float,       # Second derivative
        saturation_score: float,
        avg_volume: float,         # Average interest value
        current_value: float
    ) -> str:
        """
        Classify lifecycle stage based on multiple signals.
        
        Args:
            z_score: Statistical significance
            short_term_slope: 7-day trend slope
            long_term_slope: 30-day trend slope
            acceleration: Rate of change of slope
            saturation_score: Market saturation (0-100)
            avg_volume: Average search interest (0-100)
            current_value: Current interest value
            
        Returns:
            Lifecycle stage: Emerging, Breakout, Mainstream, Saturated, Declining
        """
        
        # DECLINING: Negative trends across the board
        if short_term_slope < -1.0 and long_term_slope < 0 and z_score < 1.0:
            return "Declining"
        
        # SATURATED: High competition, slowing growth
        if saturation_score > 70 and acceleration < 0 and avg_volume > 60:
            return "Saturated"
        
        # BREAKOUT: Strong spike with momentum
        if z_score > 2.5 and short_term_slope > 2.0 and saturation_score < 60:
            return "Breakout"
        
        # MAINSTREAM: High volume but flattening
        if avg_volume > 70 and abs(acceleration) < 0.5 and saturation_score > 50:
            return "Mainstream"
        
        # EMERGING: Low saturation, positive acceleration, growing
        if saturation_score < 40 and acceleration > 0 and short_term_slope > 0:
            return "Emerging"
        
        # Default: Early Emerging if low volume and positive
        if avg_volume < 30 and short_term_slope > 0:
            return "Emerging"
        
        # Fallback
        return "Mainstream"

    def calculate_slopes(self, values: List[float], dates: List[str]) -> Dict[str, float]:
        """
        Calculate short-term (7d), long-term (30d) slopes and acceleration.
        
        Args:
            values: Time series values
            dates: Corresponding dates
            
        Returns:
            Dict with short_term_slope, long_term_slope, acceleration
        """
        if not values or len(values) < 7:
            return {
                "short_term_slope": 0.0,
                "long_term_slope": 0.0,
                "acceleration": 0.0
            }
        
        values_arr = np.array(values, dtype=float)
        n = len(values_arr)
        
        # Short-term slope (last 7 days or available)
        short_window = min(7, n)
        recent_values = values_arr[-short_window:]
        x_short = np.arange(short_window)
        short_term_slope = np.polyfit(x_short, recent_values, 1)[0] if len(recent_values) > 1 else 0.0
        
        # Long-term slope (last 30 days or available)
        long_window = min(30, n)
        long_values = values_arr[-long_window:]
        x_long = np.arange(long_window)
        long_term_slope = np.polyfit(x_long, long_values, 1)[0] if len(long_values) > 1 else 0.0
        
        # Acceleration (change in slope)
        # Compare first half vs second half slope
        if n >= 14:
            mid = n // 2
            first_half = values_arr[:mid]
            second_half = values_arr[mid:]
            
            x_first = np.arange(len(first_half))
            x_second = np.arange(len(second_half))
            
            slope_1 = np.polyfit(x_first, first_half, 1)[0] if len(first_half) > 1 else 0.0
            slope_2 = np.polyfit(x_second, second_half, 1)[0] if len(second_half) > 1 else 0.0
            
            acceleration = slope_2 - slope_1
        else:
            acceleration = 0.0
        
        return {
            "short_term_slope": float(short_term_slope),
            "long_term_slope": float(long_term_slope),
            "acceleration": float(acceleration)
        }

    def get_lifecycle_color(self, lifecycle: str) -> str:
        """
        Return color code for frontend visualization.
        
        Args:
            lifecycle: Lifecycle stage
            
        Returns:
            Color code (hex or name)
        """
        color_map = {
            "Emerging": "#10b981",      # Green
            "Breakout": "#f59e0b",      # Amber
            "Mainstream": "#3b82f6",    # Blue
            "Saturated": "#ef4444",     # Red
            "Declining": "#6b7280"      # Gray
        }
        return color_map.get(lifecycle, "#9ca3af")

    def get_lifecycle_description(self, lifecycle: str) -> str:
        """
        Return human-readable description of lifecycle stage.
        
        Args:
            lifecycle: Lifecycle stage
            
        Returns:
            Description string
        """
        descriptions = {
            "Emerging": "Early growth phase with low competition. High opportunity.",
            "Breakout": "Rapid spike with strong momentum. Act fast.",
            "Mainstream": "Peak interest but competitive. Target differentiation.",
            "Saturated": "Crowded market with slowing growth. Difficult entry.",
            "Declining": "Falling interest. Avoid or pivot strategy."
        }
        return descriptions.get(lifecycle, "Unknown lifecycle stage")
