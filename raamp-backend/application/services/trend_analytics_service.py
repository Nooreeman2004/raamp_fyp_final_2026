# Application Layer - Trend Analytics Service
import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel

logger = logging.getLogger(__name__)

class TrendAnalyticsService:
    """Service for providing analytics data for trend dashboards"""

    async def get_live_feed(self, user_email: str, location: str = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get the latest detected spikes for the user's live feed"""
        query = {"user_id": user_email}
        if location and location.upper() != "GLOBAL":
            query["location"] = location.upper()
            
        # Try to match detections with their parent TrendSignal to get rich metadata if needed.
        # However, for speed, we'll assume TrendSignalModel is the source of truth for "Live" high-level trends if we want social scores.
        # But TrendDetectionModel stores "Spikes".
        # Let's see if we can get the latest TrendSignal to augment.
        
        # NOTE: Ideally TrendDetectionModel should also store these scores at the spike level.
        # For now, let's keep the detections simple but if we have a matching TrendSignal, we could use it per keyword.
        # We can simulate social score if not present.
        
        # Fetch detections from database
        detections = await TrendDetectionModel.find(query).sort("-detected_at").limit(limit).to_list()
        
        results = [
            {
                "id": str(d.id),
                "keyword": d.keyword,
                "niche": d.niche,
                "location": d.location,
                "score": round(d.z_score, 2),
                "z_score_spike": round(d.z_score, 2),  # Frontend compatibility
                "impact": d.impact_level,
                "detected_at": d.detected_at,
                "current_value": d.current_value,
                "is_spike": True,
                "sentiment": "POSITIVE" if d.sentiment_score > 0 else "NEUTRAL",
                # Use stored or calculated metrics
                "arbitrage_score": round((d.z_score * 5) + (100 - d.current_value) / 2, 2),
                "profitability": round((d.z_score * 5) + (100 - d.current_value) / 2, 2), # Arbitrage Score Proxy
                "confidence": round(0.85 + (min(d.z_score, 10)/50), 2),
                "time_diff": "just now",
                # New Fields
                "social_score": float(d.z_score * 8) if d.z_score else 0, # Placeholder if not in DB model yet
                "saturation_score": d.current_value, # Proxy
                "is_real_social": False, # Will be enriched below if matching signal found
                "is_real_saturation": False,
                # ENHANCEMENT: New lifecycle, prediction, and profit fields
                "lifecycle_stage": d.lifecycle_stage or "Mainstream",
                "predicted_growth_pct": d.predicted_growth_pct or 0.0,
                "breakout_probability": d.breakout_probability or 0.0,
                "profit_score": d.profit_score or 50.0,
                "timeframe": d.timeframe or "30d"
            }
            for d in detections
        ]

        # Enrich with real flags from latest signals if possible
        if results:
            latest_signals = await TrendSignalModel.find({"user_email": user_email}).sort("-created_at").limit(5).to_list()
            signal_map = {s.keywords[0].lower(): s for s in latest_signals if s.keywords}
            for r in results:
                match = signal_map.get(r['keyword'].lower())
                if match:
                    r['is_real_social'] = match.is_real_social
                    r['is_real_saturation'] = match.is_real_saturation

        # If no spikes, show "Baseline Trends" from TrendSignal (Layer 1 Source)
        if not results:
            signal_query = {"user_email": user_email, "fetch_status": "completed"}
            if location and location.upper() != "GLOBAL":
                signal_query["location"] = location.upper()
            
            latest_signal = await TrendSignalModel.find(signal_query).sort("-created_at").first_or_none()
            if latest_signal and latest_signal.keywords:
                # Create baseline trends from the signal's keywords
                logger.info("No spikes found, creating baseline trends from signal %s", str(latest_signal.id))
                logger.info("📊 Signal data available - Keywords: %d, Geo data: %s, Rising queries: %s", 
                           len(latest_signal.keywords), 
                           bool(latest_signal.geo_data),
                           bool(latest_signal.rising_queries))
                
                # Main trend from enriched data
                if latest_signal.social_score and latest_signal.social_score > 0:
                    results.append({
                        "id": str(latest_signal.id),
                        "keyword": latest_signal.keywords[0],
                        "niche": latest_signal.niche,
                        "location": latest_signal.location,
                        "score": round(latest_signal.arbitrage_score / 10, 2) if latest_signal.arbitrage_score else 3.0,
                        "z_score_spike": 1.5,  # Below threshold but visible
                        "impact": "BASELINE",
                        "detected_at": latest_signal.fetched_at or latest_signal.created_at,
                        "current_value": latest_signal.saturation_score or 50,
                        "is_spike": False,
                        "label": "BASELINE",
                        "sentiment": "NEUTRAL",
                        "arbitrage_score": latest_signal.arbitrage_score or 50,
                        "profitability": latest_signal.arbitrage_score or 50,
                        "confidence": 0.70,
                        "time_diff": "just now",
                        "social_score": latest_signal.social_score or 50,
                        "saturation_score": latest_signal.saturation_score or 50,
                        "hashtags": latest_signal.hashtags[:3] if latest_signal.hashtags else [],
                        "is_real_social": latest_signal.is_real_social,
                        "is_real_saturation": latest_signal.is_real_saturation,
                        "lifecycle_stage": latest_signal.lifecycle_stage or "Mainstream",
                        "predicted_growth_pct": latest_signal.predicted_growth_pct or 0.0,
                        "breakout_probability": latest_signal.breakout_probability or 0.0,
                        "profit_score": latest_signal.profit_score or 50.0,
                        "timeframe": latest_signal.timeframe or "30d"
                    })

                # Add rising queries as additional baseline trends
                if latest_signal.rising_queries:
                    for queries in latest_signal.rising_queries.values():
                        for q in queries[:3]:  # Top 3 rising queries
                            results.append({
                                "id": f"rising_{len(results)}",
                                "keyword": q.get("query"),
                                "niche": latest_signal.niche,
                                "location": latest_signal.location,
                                "score": min(q.get("value", 0) / 100, 10.0),  # Normalize to 0-10 scale
                                "z_score_spike": min(q.get("value", 0) / 50, 2.5),  # Scale for display
                                "impact": "RISING" if q.get("value", 0) > 100 else "EMERGING",
                                "detected_at": latest_signal.fetched_at or latest_signal.created_at,
                                "current_value": 20,  # Low saturation for rising queries
                                "is_spike": False,
                                "label": "RISING",
                                "sentiment": "POSITIVE",
                                "arbitrage_score": 60,
                                "profitability": 60,
                                "confidence": 0.65,
                                "time_diff": "just now",
                                "social_score": 50,
                                "saturation_score": 20,
                                "lifecycle_stage": "Emerging",
                                "predicted_growth_pct": q.get("value", 0),
                                "breakout_probability": min(q.get("value", 0) / 2, 100),
                                "profit_score": 60.0,
                                "timeframe": "30d"
                            })
                
                # Sort by score and limit
                results.sort(key=lambda x: x["score"] if isinstance(x["score"], (int, float)) else 0, reverse=True)
                results = results[:limit]
            else:
                logger.warning("No completed trend signals found for user %s", user_email)

        return results

    async def get_geo_heatmap(self, user_email: str, location: str = None) -> List[Dict[str, Any]]:
        """Get geographic intensity data with coordinates for map visualization"""
        query = {"user_email": user_email}
        if location and location.upper() != "GLOBAL":
            query["location"] = location.upper()

        latest_signal = await TrendSignalModel.find(query).sort("-created_at").first_or_none()
        
        # approximate coordinates for major PK/Global cities to simulate map
        # Coordinate mapping for Regions (Provinces/States) instead of Cities
        # Google Trends interest_by_region returns Region names, not City names
        region_coords = {
            # Pakistan Provinces/Regions
            "SINDH": {"x": 25, "y": 80}, 
            "PUNJAB": {"x": 65, "y": 60}, 
            "ISLAMABAD CAPITAL TERRITORY": {"x": 68, "y": 45}, 
            "KHYBER PAKHTUNKHWA": {"x": 55, "y": 35},
            "BALOCHISTAN": {"x": 20, "y": 60}, 
            "GILGIT-BALTISTAN": {"x": 75, "y": 15},
            "AZAD JAMMU AND KASHMIR": {"x": 80, "y": 30},
            
            # US States (Major)
            "CALIFORNIA": {"x": 10, "y": 60},
            "NEW YORK": {"x": 90, "y": 30},
            "TEXAS": {"x": 45, "y": 80},
            "FLORIDA": {"x": 80, "y": 90},
            "ILLINOIS": {"x": 65, "y": 40},
            "WASHINGTON": {"x": 15, "y": 10},
            
            # UK Regions (Major)
            "ENGLAND": {"x": 60, "y": 70},
            "SCOTLAND": {"x": 50, "y": 30},
            "WALES": {"x": 40, "y": 75},
            
            # Fallback Cities (just in case)
            "KARACHI": {"x": 25, "y": 85}, 
            "LAHORE": {"x": 70, "y": 60},
            "ISLAMABAD": {"x": 68, "y": 45}
        }

        if not latest_signal or not latest_signal.geo_data:
            # Fallback if no specific data, return empty list or defaults
            has_signal = bool(latest_signal)
            has_geo = bool(latest_signal.geo_data) if latest_signal else False
            logger.warning("📍 No geo_data available for user %s. Signal found: %s, Geo data: %s", 
                         user_email, has_signal, has_geo)
            return []
            
        results = []
        for region, keywords in latest_signal.geo_data.items():
            # Handle nested dictionary if present (some pytrends versions)
            if isinstance(keywords, dict):
                keyword_items = keywords.items()
            else:
                continue

            for keyword, value in keyword_items:
                region_upper = region.upper()
                # Try exact match first, then partial match
                coords = region_coords.get(region_upper)
                if not coords:
                    coords = {"x": 50, "y": 50} # Default center
                    # Simple heuristic distribution for unknown regions to avoid stacking
                    import hashlib
                    h = int(hashlib.md5(region_upper.encode()).hexdigest(), 16)
                    coords = {"x": (h % 80) + 10, "y": (h % 60) + 20}

                # Add Jitter to simulate "Heat" clusters (prevent stacking)
                import random
                jitter_x = random.uniform(-2.5, 2.5)
                jitter_y = random.uniform(-1.5, 1.5)

                results.append({
                    "keyword": keyword,
                    "city": region, # Keep original name
                    "intensity": value,
                    "x": max(0, min(100, coords["x"] + jitter_x)),
                    "y": max(0, min(100, coords["y"] + jitter_y)),
                    "delta": f"+{round(value * 0.15, 1)}%", # Simulated local delta
                    "velocity": "HIGH" if value > 80 else "MEDIUM"
                })
        
        # Sort by intensity to show most relevant regions first
        results.sort(key=lambda x: x["intensity"], reverse=True)
        return results[:15] # Top 15 regions

    async def get_spike_timeline(self, user_email: str, days: int = 30, location: str = None) -> List[Dict[str, Any]]:
        """Get timeline of trend spikes over the last X days"""
        start_date = datetime.utcnow() - timedelta(days=days)
        query = {
            "user_id": user_email,
            "detected_at": {"$gte": start_date}
        }
        if location and location.upper() != "GLOBAL":
            query["location"] = location.upper()

        detections = await TrendDetectionModel.find(query).sort("detected_at").to_list()
        
        # Group by date
        timeline = {}
        for d in detections:
            date_str = d.detected_at.strftime("%Y-%m-%d")
            if date_str not in timeline:
                timeline[date_str] = {"date": date_str, "count": 0, "avg_z": 0.0}
            timeline[date_str]["count"] += 1
            timeline[date_str]["avg_z"] += d.z_score
            
        # Finalize averages
        for date in timeline:
            timeline[date]["avg_z"] = round(timeline[date]["avg_z"] / timeline[date]["count"], 2)

        # FALLBACK: If no spikes, show Interest Over Time from the latest signal
        if not timeline:
            signal_query = {"user_email": user_email}
            if location and location.upper() != "GLOBAL":
                signal_query["location"] = location.upper()
            
            latest_signal = await TrendSignalModel.find(signal_query).sort("-created_at").first_or_none()
            if latest_signal and latest_signal.search_interest:
                dates = latest_signal.search_interest.get("dates", [])
                data = latest_signal.search_interest.get("data", {})
                
                for i, date_str in enumerate(dates):
                    # Sum up interest across all keywords for a general "Topic Velocity"
                    total_interest = sum([vals[i] for vals in data.values() if i < len(vals)])
                    avg_interest = total_interest / len(data) if data else 0
                    
                    timeline[date_str] = {
                        "date": date_str,
                        "count": round(avg_interest, 1), # Use average interest as "count" proxy
                        "avg_z": 0 # No Z-score for raw interest
                    }
            
        return sorted(list(timeline.values()), key=lambda x: x["date"])

    async def get_market_gap_data(self, user_email: str, location: str = None) -> List[Dict[str, Any]]:
        """
        Get data for the Sweet Spot Matrix (Saturation vs Velocity).
        X-axis: Saturation (Current Value 0-100)
        Y-axis: Velocity (Z-Score)
        """
        query = {"user_id": user_email}
        if location and location.upper() != "GLOBAL":
            query["location"] = location.upper()

        detections = await TrendDetectionModel.find(query).sort("-detected_at").limit(30).to_list()
        
        logger.info("⚫ Bubble chart query found %d detections for user %s", len(detections), user_email)
        
        results = []
        for d in detections:
            # Use stored profit score or calculate arbitrage score as fallback
            profit_score = d.profit_score if d.profit_score is not None else round((d.z_score * 5) + (100 - d.current_value) / 2, 2)
            
            # Determine Quadrant based on lifecycle or traditional logic
            if d.lifecycle_stage:
                quadrant_map = {
                    "Emerging": "Gold Mine",
                    "Breakout": "Gold Mine",
                    "Mainstream": "Crowded",
                    "Saturated": "Fading",
                    "Declining": "Low Opportunity"
                }
                quadrant = quadrant_map.get(d.lifecycle_stage, "Low Opportunity")
            else:
                # Fallback to traditional logic
                quadrant = "Low Opportunity"
                if d.z_score > 3.0 and d.current_value < 40:
                    quadrant = "Gold Mine"
                elif d.z_score > 3.0 and d.current_value >= 40:
                    quadrant = "Crowded"
                elif d.z_score <= 3.0 and d.current_value > 60:
                    quadrant = "Fading"
            
            results.append({
                "keyword": d.keyword,
                "velocity": round(d.z_score, 2),        # Y-axis
                "saturation": d.current_value,          # X-axis
                "arbitrage_score": profit_score,        # Bubble size (now using profit score)
                "quadrant": quadrant,                   # Color logic
                "impact": d.impact_level,
                # ENHANCEMENT: Add new fields
                "lifecycle_stage": d.lifecycle_stage or "Mainstream",
                "breakout_probability": d.breakout_probability or 0.0,
                "profit_score": profit_score,
                "timeframe": d.timeframe or "30d",
                "is_real_social": False,
                "is_real_saturation": False
            })

        # Enrich flags
        if results:
            latest_signals = await TrendSignalModel.find({"user_email": user_email}).sort("-created_at").limit(10).to_list()
            signal_map = {s.keywords[0].lower(): s for s in latest_signals if s.keywords}
            for r in results:
                match = signal_map.get(r['keyword'].lower())
                if match:
                    r['is_real_social'] = match.is_real_social
                    r['is_real_saturation'] = match.is_real_saturation
            
        # Optimization: Fetch latest TrendSignal to mix in broader market context if needed
        # but the request was specifically to use the new service logic.
        # Since TrendDetectionService updates TrendSignal, we should probably fetch from TrendSignal for the "Opportunities" chart?
        # The prompt implies "TrendAnalyticsService (extend)... Output structured TrendSignal objects."
        # The current implementation of get_market_gap_data iterates detections (spikes).
        # Let's check if we can fetch from TrendSignals directly for broader market view.
        
        if not results:
             # Fallback to latest TrendSignal
            logger.info("⚫ No detections found, checking for fallback TrendSignal data")
            signal_query = {"user_email": user_email}
            if location and location.upper() != "GLOBAL":
                signal_query["location"] = location.upper()
            
            latest_signal = await TrendSignalModel.find(signal_query).sort("-created_at").first_or_none()
            has_signal = bool(latest_signal)
            has_arbitrage = bool(latest_signal.arbitrage_score) if latest_signal else False
            logger.info("⚫ Fallback signal found: %s, Has arbitrage_score: %s", has_signal, has_arbitrage)
            if latest_signal and latest_signal.arbitrage_score:
                # Use the computed Layer 1 scores from the signal itself (top keyword)
                results.append({
                    "keyword": latest_signal.keywords[0] if latest_signal.keywords else "Market Trend",
                    "velocity": round(latest_signal.social_score / 10, 2) if latest_signal.social_score else 5.0, # Proxy
                    "saturation": latest_signal.saturation_score or 50,
                    "arbitrage_score": latest_signal.arbitrage_score or 50,
                    "quadrant": "Gold Mine" if (latest_signal.arbitrage_score or 0) > 70 else "Crowded",
                    "impact": "HIGH",
                    "is_real_social": latest_signal.is_real_social,
                    "is_real_saturation": latest_signal.is_real_saturation
                })
                 
        return results
    
    async def get_platform_reach(self, user_email: str, location: str = None) -> Dict[str, Any]:
        """Get estimate of reach across different platforms (Google, Instagram, Facebook)"""
        query = {"user_email": user_email}
        if location and location.upper() != "GLOBAL":
            query["location"] = location.upper()
            
        latest_signal = await TrendSignalModel.find(query).sort("-created_at").first_or_none()
        
        if not latest_signal:
            return {"google": 50, "instagram": 30, "facebook": 20, "total_reach": "0"}
            
        # Base logic: If niche is lifestyle/fashion -> higher social reach. 
        # If niche is B2B/Tech -> higher search reach.
        niche = latest_signal.niche.lower()
        social_friendly = ["fashion", "food", "lifestyle", "travel", "fitness", "beauty"]
        
        is_social = any(s in niche for s in social_friendly)
        
        if is_social:
            reach = {"google": 30, "instagram": 45, "facebook": 25}
        else:
            reach = {"google": 60, "instagram": 25, "facebook": 15}
            
        # Add some randomness based on rising query count
        query_count = sum(len(q) for q in latest_signal.rising_queries.values())
        if query_count > 10:
            reach["instagram"] += 5
            reach["google"] -= 5
            
        reach["total_reach"] = f"{min(99, 40 + query_count * 2)}%"
        return reach
