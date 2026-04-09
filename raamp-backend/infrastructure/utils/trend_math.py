# Infrastructure Layer - Trend Detection Mathematical Logic
import numpy as np
import pandas as pd
from typing import List, Dict, Optional
from domain.entities.trend_detection import TrendSpike, TrendDetectionConfig


class TrendDetectionEngine:
    """Mathematical engine for detecting spikes in time-series trend data"""
    
    @staticmethod
    def detect_spikes(
        dates: List[str],
        values: List[float],
        keyword: str,
        niche: str,
        location: str,
        config: TrendDetectionConfig = TrendDetectionConfig()
    ) -> List[TrendSpike]:
        """
        Detect spikes using EWMA and Rolling Z-Score.
        Returns a list of TrendSpike objects.
        """
        if len(values) < config.min_data_points:
            return []
            
        # Convert to pandas series for easy calculation
        s = pd.Series(values)
        
        # 1. Calculate EWMA (Exponential Weighted Moving Average)
        # EWMA helps smooth the baseline while being responsive to recent changes
        ewma = s.ewm(alpha=config.alpha, adjust=False).mean()
        
        # 2. Calculate Rolling Mean and Standard Deviation for Z-Score
        rolling_mean = s.rolling(window=config.rolling_window, min_periods=1).mean()
        rolling_std = s.rolling(window=config.rolling_window, min_periods=1).std()
        
        # 3. Calculate Z-Score
        # Z = (Value - Mean) / StdDev
        # We use a small epsilon to avoid division by zero
        eps = 1e-9
        z_scores = (s - rolling_mean) / (rolling_std + eps)
        
        spikes = []

        # Scan the full series for spike events. We'll tag the last 3 points as "recent"
        # so downstream can decide whether to notify vs just persist for analytics.
        recent_start = max(0, len(values) - 3)

        for i in range(0, len(values)):
            z = z_scores.iloc[i]
            val = values[i]
            expected = ewma.iloc[i]
            
            # Check if current value exceeds threshold and is significantly higher than expected
            if z > config.threshold and val > expected:
                spikes.append(TrendSpike(
                    keyword=keyword,
                    z_score=float(z),
                    current_value=float(val),
                    expected_value=float(expected),
                    timestamp=pd.to_datetime(dates[i]),
                    niche=niche,
                    location=location,
                    is_recent=bool(i >= recent_start),
                ))
                
        return spikes
