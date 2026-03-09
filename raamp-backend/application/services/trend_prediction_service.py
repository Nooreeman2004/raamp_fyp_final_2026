
# Application Layer - Trend Prediction Service
import logging
from typing import List, Dict, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class TrendPredictionService:
    """
    Lightweight trend prediction service using linear regression and statistical methods.
    No LSTM, no paid APIs, no heavy frameworks.
    """

    def predict_trend(
        self,
        values: List[float],
        forecast_days: int = 7
    ) -> Dict:
        """
        Predict future trend values using linear regression.
        
        Args:
            values: Historical time series values
            forecast_days: Number of days to forecast (default 7)
            
        Returns:
            Dict containing:
                - forecast_series: List of predicted values
                - predicted_growth_pct: Growth percentage
                - breakout_probability: 0-100 score
        """
        if not values or len(values) < 7:
            return {
                "forecast_series": [],
                "predicted_growth_pct": 0.0,
                "breakout_probability": 0.0
            }
        
        values_arr = np.array(values, dtype=float)
        n = len(values_arr)
        
        # Linear regression fit
        x = np.arange(n)
        coefficients = np.polyfit(x, values_arr, 1)  # y = mx + b
        slope, intercept = coefficients
        
        # Generate forecast
        forecast_x = np.arange(n, n + forecast_days)
        forecast_values = slope * forecast_x + intercept
        
        # Clip to 0-100 range (Google Trends values)
        forecast_values = np.clip(forecast_values, 0, 100)
        
        # Calculate predicted growth percentage
        current_value = values_arr[-1]
        final_forecast = forecast_values[-1]
        
        if current_value > 0:
            growth_pct = ((final_forecast - current_value) / current_value) * 100
        else:
            growth_pct = 0.0
        
        # Calculate breakout probability
        breakout_prob = self._calculate_breakout_probability(
            values_arr, 
            slope, 
            forecast_values
        )
        
        return {
            "forecast_series": forecast_values.tolist(),
            "predicted_growth_pct": float(growth_pct),
            "breakout_probability": float(breakout_prob)
        }

    def _calculate_breakout_probability(
        self,
        values: np.ndarray,
        slope: float,
        forecast: np.ndarray
    ) -> float:
        """
        Calculate breakout probability based on slope strength, volatility, and momentum.
        
        Args:
            values: Historical values
            slope: Trend slope
            forecast: Forecasted values
            
        Returns:
            Breakout probability (0-100)
        """
        # Factor 1: Slope strength (higher = more likely)
        # Normalize slope: 0 = 0%, 5+ = 100%
        slope_factor = min(100, abs(slope) * 20) if slope > 0 else 0
        
        # Factor 2: Low volatility = more predictable = higher probability
        if len(values) > 3:
            volatility = np.std(values)
            # High volatility reduces confidence
            volatility_penalty = min(30, volatility / 2)
        else:
            volatility_penalty = 0
        
        # Factor 3: Current momentum (recent values trending up)
        recent_window = min(7, len(values))
        recent_values = values[-recent_window:]
        recent_trend = np.mean(np.diff(recent_values)) if len(recent_values) > 1 else 0
        momentum_factor = min(30, max(0, recent_trend * 10))
        
        # Factor 4: Forecast consistency (are we predicting growth?)
        forecast_growth = (forecast[-1] - values[-1]) / max(1, values[-1]) * 100
        growth_factor = min(20, max(0, forecast_growth / 2))
        
        # Combine factors
        breakout_prob = slope_factor + momentum_factor + growth_factor - volatility_penalty
        
        # Clip to 0-100
        return float(np.clip(breakout_prob, 0, 100))

    def get_confidence_interval(
        self,
        values: List[float],
        confidence: float = 0.95
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate confidence interval for predictions.
        
        Args:
            values: Historical values
            confidence: Confidence level (default 0.95)
            
        Returns:
            Tuple of (lower_bound, upper_bound) lists
        """
        if not values or len(values) < 3:
            return [], []
        
        values_arr = np.array(values, dtype=float)
        std_dev = np.std(values_arr)
        
        # Z-score for confidence level
        z_score = 1.96 if confidence == 0.95 else 2.576  # 95% or 99%
        
        margin = z_score * std_dev
        
        lower = (values_arr - margin).tolist()
        upper = (values_arr + margin).tolist()
        
        return lower, upper

    def detect_seasonality(self, values: List[float], period: int = 7) -> bool:
        """
        Detect if there's weekly seasonality in the data.
        
        Args:
            values: Time series values
            period: Period to check (default 7 for weekly)
            
        Returns:
            True if seasonality detected
        """
        if len(values) < period * 2:
            return False
        
        values_arr = np.array(values, dtype=float)
        
        # Simple autocorrelation check
        mean_val = np.mean(values_arr)
        
        # Split into periods
        n_periods = len(values_arr) // period
        periods = [values_arr[i*period:(i+1)*period] for i in range(n_periods)]
        
        if len(periods) < 2:
            return False
        
        # Check correlation between periods
        period_means = [np.mean(p) for p in periods]
        correlation = np.corrcoef(period_means[:-1], period_means[1:])[0, 1] if len(period_means) > 1 else 0
        
        # High correlation indicates seasonality
        return correlation > 0.6

    def calculate_trend_strength(self, values: List[float]) -> float:
        """
        Calculate overall trend strength (0-100).
        
        Args:
            values: Time series values
            
        Returns:
            Trend strength score
        """
        if not values or len(values) < 3:
            return 0.0
        
        values_arr = np.array(values, dtype=float)
        
        # Linear fit R-squared
        x = np.arange(len(values_arr))
        coefficients = np.polyfit(x, values_arr, 1)
        fitted_values = np.polyval(coefficients, x)
        
        # R-squared calculation
        ss_res = np.sum((values_arr - fitted_values) ** 2)
        ss_tot = np.sum((values_arr - np.mean(values_arr)) ** 2)
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Convert to 0-100 scale
        return float(np.clip(r_squared * 100, 0, 100))
