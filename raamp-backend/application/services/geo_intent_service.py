# Application Layer - Geo-Intent Marketing Engine Service
import asyncio
import logging
import math
import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import BackgroundTasks

from application.services.geo_intent_fetchers import ingest_all_signals
from infrastructure.database.models.heat_score_model import HeatScoreModel
from infrastructure.database.models.campaign_log_model import CampaignLogModel
from infrastructure.database.models.campaign_brief_model import CampaignBriefModel
from infrastructure.database.models.user_model import UserModel
from application.services.credit_service import get_credit_service

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Weight constants
# ---------------------------------------------------------------------------
_W_TRENDS: float = 0.35
_W_PLACES: float = 0.40
_W_WEATHER: float = 0.25


# ---------------------------------------------------------------------------
# Urgency classification
# ---------------------------------------------------------------------------

def classify_urgency(score: int) -> str:
    """Map integer score (0–100) to urgency label."""
    if score >= 90:
        return "Critical"
    if score >= 61:
        return "High"
    if score >= 31:
        return "Medium"
    return "Low"


# ---------------------------------------------------------------------------
# Heat Score Calculation
# ---------------------------------------------------------------------------

def compute_heat_score(trends: float, places: float, weather: float) -> int:
    """
    Weighted combination of normalised signals → integer 0–100.

    Formula: (trends * 0.35 + places * 0.40 + weather * 0.25) * 100
    Result is clamped to [0, 100] and returned as an integer.
    """
    raw = (trends * _W_TRENDS + places * _W_PLACES + weather * _W_WEATHER) * 100.0
    return int(max(0, min(100, round(raw))))


# ---------------------------------------------------------------------------
# Core Service
# ---------------------------------------------------------------------------

class GeoIntentService:
    """
    Orchestrates the Geo-Intent Marketing Engine pipeline:

    1. Parallel signal ingestion (Trends + Places + Weather)
    2. Heat score calculation
    3. Urgency classification
    4. Async writes to campaign_logs and heat_scores (non-blocking)
    5. Structured response assembly
    """

    def __init__(self):
        self.credit_service = get_credit_service()

    async def compute(
        self,
        business_id: str,
        keywords: List[str],
        latitude: float,
        longitude: float,
        radius: int,
        is_indoor: bool,
        background_tasks: BackgroundTasks,
        user_id: str, # Added to handle credits
        skip_credits: bool = False,
    ) -> Dict[str, Any]:
        """
        Full geo-intent pipeline for a single business request.

        Returns a dict compatible with HeatScoreResponse.
        """
        logger.info(
            "GeoIntentService.compute — business_id=%s keywords=%s lat=%.4f lng=%.4f radius=%d indoor=%s",
            business_id,
            keywords,
            latitude,
            longitude,
            radius,
            is_indoor,
        )

        # ── Step 0: Check Credits + Tier ──────────────────────────────────
        # Geo Intent Scan = 2 credits
        if not skip_credits:
            await self.credit_service.check_and_deduct(user_id, "geo_radar_scan")
        
        user = await UserModel.find_one(UserModel.email == user_id)
        # ── DEMO OVERRIDE: Premium status for demo user ─────────────────
        if user_id.lower() == "abdullah@gmail.com":
            user_tier = "premium"
        else:
            user_tier = user.subscriptionTier if user else "free"

        # ── Step 1: Parallel signal ingestion ──────────────────────────────
        t_ingest = time.perf_counter()
        signals = await ingest_all_signals(
            keywords=keywords,
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            is_indoor=is_indoor,
            user_tier=user_tier # Added to filter signals
        )
        logger.info(
            "GeoIntentService.compute: ingest_all_signals %.2fs (tier=%s)",
            time.perf_counter() - t_ingest,
            user_tier,
        )

        trends_score: float = signals["trends"]
        places_score: float = signals["places"]
        weather_score: float = signals["weather"]
        signals_status: Dict[str, str] = signals.get("status", {})

        # ── Step 2: Heat score calculation ─────────────────────────────────
        score = compute_heat_score(trends_score, places_score, weather_score)

        # ── Step 3: Classification & Metadata ──────────────────────────────
        urgency = classify_urgency(score)
        is_critical = score >= 90
        timestamp = datetime.utcnow()
        geo_point = {"type": "Point", "coordinates": [longitude, latitude]}
        signal_map = {
            "trends_score": round(trends_score, 4),
            "places_score": round(places_score, 4),
            "weather_score": round(weather_score, 4),
        }

        # ── Step 4: Generate reasoning ─────────────────────────────────────
        reasoning_parts = []
        if trends_score > 0.6:
            reasoning_parts.append(f"We've detected a high volume of digital intent for '{keywords[0]}' in your area.")
        
        if places_score > 0.7:
            reasoning_parts.append(f"Physical crowd density is currently high within {radius/1000:.1f}KM of your location.")
        
        if weather_score > 0.6:
            reasoning_parts.append("Current weather conditions are strongly favoring customer engagement.")
        
        if not reasoning_parts:
            reasoning = "Signals are currently stable. Monitor for upcoming shifts in local demand."
        else:
            reasoning = " ".join(reasoning_parts)
            if score >= 60:
                reasoning += " This is a prime window for a targeted push."

        # ── Step 5: Non-blocking DB writes ─────────────────────────────────
        background_tasks.add_task(
            self._persist_campaign_log,
            business_id=business_id,
            keywords=keywords,
            location=geo_point,
            radius=radius,
            signals=signal_map,
            final_score=score,
            urgency=urgency,
            is_indoor=is_indoor,
            timestamp=timestamp,
        )

        background_tasks.add_task(
            self._persist_heat_score,
            business_id=business_id,
            location=geo_point,
            score=score,
            urgency=urgency,
            signals=signal_map,
            radius=radius,
            is_critical=is_critical,
            timestamp=timestamp,
        )

        logger.info(
            "GeoIntentService result — score=%d urgency=%s is_critical=%s",
            score,
            urgency,
            is_critical,
        )

        # ── Step 6: Generate Real Persona Split ───────────────────────────
        persona_split = self._calculate_persona_split(
            place_types=signals.get("place_types", []),
            trends_score=trends_score * 100,  # Convert 0-1 to 0-100
            weather_score=weather_score * 100, # Convert 0-1 to 0-100
            heat_score=score,
            hour_of_day=datetime.utcnow().hour,
            day_of_week=datetime.utcnow().weekday(),
            keywords=keywords
        )

        # ── Step 7: Generate Live Signal Feed ──────────────────────────────
        radar_feed = self._generate_radar_feed(
            keywords=keywords,
            trends_score=trends_score,
            places_score=places_score,
            weather_score=weather_score,
            place_types=signals.get("place_types", []),
            radius=radius
        )

        # ── Step 8: Structured response ────────────────────────────────────
        return {
            "score": score,
            "urgency": urgency,
            "is_critical": is_critical,
            "signals": {
                "trends_score": round(trends_score, 4),
                "places_score": round(places_score, 4),
                "weather_score": round(weather_score, 4),
            },
            "signals_status": signals_status,
            "reasoning": reasoning,
            "persona_split": persona_split,
            "radar_feed": radar_feed,
            # Useful for internal consumers (e.g. arbitrage prompt localization). Safe extra field.
            "place_types": signals.get("place_types", []),
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius / 1000.0,
            "timestamp": timestamp,
        }

    def _generate_zone_points(
        self,
        lat: float,
        lng: float,
        radius_m: int,
        num_points: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Generate points in a ring around the center at ~radius_m distance.
        Returns list of {lat, lng, label} dicts.
        """
        points: List[Dict[str, Any]] = []
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        n = max(1, min(num_points, 8))
        for i in range(n):
            angle = (360 / n) * i
            angle_rad = math.radians(angle)
            r_earth = 6371000.0
            d_lat = (radius_m * math.cos(angle_rad)) / r_earth
            d_lng = (radius_m * math.sin(angle_rad)) / (
                r_earth * math.cos(math.radians(lat))
            )
            points.append(
                {
                    "lat": lat + math.degrees(d_lat),
                    "lng": lng + math.degrees(d_lng),
                    "label": directions[i],
                }
            )
        return points

    async def recommend_zones(
        self,
        business_id: str,
        keywords: List[str],
        latitude: float,
        longitude: float,
        radius: int,
        is_indoor: bool,
        user_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Score surrounding zones in parallel, return top 3 ranked.
        Credits are deducted once by the router, not per zone.
        """
        _ = business_id  # reserved for future persistence / analytics

        user = await UserModel.find_one(UserModel.email == user_id)
        if user_id.lower() == "abdullah@gmail.com":
            user_tier = "premium"
        else:
            user_tier = user.subscriptionTier if user else "free"

        try:
            env_n = int(os.getenv("RAAMP_ZONE_NUM_POINTS", "4"))
        except ValueError:
            env_n = 4
        n_zones = max(4, min(env_n, 8))

        zone_points = self._generate_zone_points(latitude, longitude, radius, num_points=n_zones)
        logger.info(
            "recommend_zones: start n_zones=%d radius_m=%d user=%s",
            len(zone_points),
            radius,
            user_id,
        )
        t_zones = time.perf_counter()

        async def score_zone(point: Dict[str, Any]) -> Dict[str, Any]:
            signals = await ingest_all_signals(
                keywords=keywords,
                latitude=point["lat"],
                longitude=point["lng"],
                radius=radius,
                is_indoor=is_indoor,
                user_tier=user_tier,
            )
            score = compute_heat_score(
                signals["trends"],
                signals["places"],
                signals["weather"],
            )
            urgency = classify_urgency(score)

            dominant = max(
                [
                    ("trends", signals["trends"]),
                    ("places", signals["places"]),
                    ("weather", signals["weather"]),
                ],
                key=lambda x: x[1],
            )
            signal_labels = {
                "trends": "high search intent",
                "places": "high foot traffic density",
                "weather": "favorable weather conditions",
            }
            reason = f"{signal_labels[dominant[0]]} in this zone"

            return {
                "label": point["label"],
                "latitude": point["lat"],
                "longitude": point["lng"],
                "score": score,
                "urgency": urgency,
                "reason": reason,
                "signals": {
                    "trends_score": round(signals["trends"], 3),
                    "places_score": round(signals["places"], 3),
                    "weather_score": round(signals["weather"], 3),
                },
            }

        results = await asyncio.gather(*[score_zone(p) for p in zone_points])
        ranked = sorted(results, key=lambda x: x["score"], reverse=True)
        logger.info(
            "recommend_zones: done in %.2fs (parallel ingest per zone) n_zones=%d user=%s",
            time.perf_counter() - t_zones,
            len(zone_points),
            user_id,
        )
        return ranked[:3]

    def _calculate_persona_split(
        self,
        place_types: List[str],
        trends_score: float = 50.0,      # 0-100
        weather_score: float = 50.0,     # 0-100  
        heat_score: float = 50.0,        # 0-100
        hour_of_day: int = 12,           # 0-23 UTC
        day_of_week: int = 1,            # 0=Monday, 6=Sunday
        keywords: List[str] = []         # user-tracked keywords
    ) -> List[Dict[str, Any]]:
        """
        Calculate persona distribution based on nearby place categories and real-world signals.
        Uses a multi-signal approach combining POI density, time of day, weather, 
        and search intent to produce a defensible, dynamic audience breakdown.
        """
        if not place_types:
            return [
                {"type": "Mixed Transit", "pct": 100, "desc": "Balanced distribution detected — insufficient POI density for specific persona targeting."}
            ]
        
        # 1. Base POI-based counts
        mapping = {
            "Office Commuters": ["office", "establishment", "employer", "accounting", "bank", "lawyer"],
            "Retail Shoppers": ["shopping_mall", "clothing_store", "store", "electronics_store", "jewelry_store", "shoe_store"],
            "Food Visitors": ["restaurant", "cafe", "food", "bar", "bakery", "meal_takeaway"],
            "Local Residents": ["local_government_office", "neighborhood", "real_estate_agency", "park", "gym", "mosque", "church", "synagogue"],
            "Students": ["school", "university", "library", "secondary_school", "primary_school"]
        }
        
        raw_scores = {cat: 0.0 for cat in mapping}
        total_pois = 0
        
        for t in place_types:
            for cat, cat_keywords in mapping.items():
                if any(kw == t for kw in cat_keywords):
                    raw_scores[cat] += 1.0
                    total_pois += 1
                    break
        
        if total_pois == 0:
            return [{"type": "Mixed Transit", "pct": 100, "desc": "Balanced distribution detected — insufficient POI density for specific persona targeting."}]

        # 2. Apply Dynamic Modifiers
        is_weekday = day_of_week < 5
        
        # MODIFIER 1 — Time of Day (UTC)
        if is_weekday:
            if 7 <= hour_of_day <= 10:  # Morning
                raw_scores["Office Commuters"] *= 1.4
                raw_scores["Students"] *= 1.3
                raw_scores["Food Visitors"] *= 1.1
                raw_scores["Retail Shoppers"] *= 0.7
                raw_scores["Local Residents"] *= 0.8
            elif 11 <= hour_of_day <= 14:  # Lunch
                raw_scores["Food Visitors"] *= 1.5
                raw_scores["Retail Shoppers"] *= 1.2
                raw_scores["Office Commuters"] *= 0.9
                raw_scores["Students"] *= 1.1
                raw_scores["Local Residents"] *= 1.0
            elif 17 <= hour_of_day <= 21:  # Evening
                raw_scores["Retail Shoppers"] *= 1.4
                raw_scores["Food Visitors"] *= 1.3
                raw_scores["Local Residents"] *= 1.2
                raw_scores["Office Commuters"] *= 0.6
                raw_scores["Students"] *= 0.8
        else: # Weekend
            if 10 <= hour_of_day <= 18:
                raw_scores["Retail Shoppers"] *= 1.5
                raw_scores["Food Visitors"] *= 1.4
                raw_scores["Local Residents"] *= 1.3
                raw_scores["Students"] *= 0.6
                raw_scores["Office Commuters"] *= 0.3
        
        # Late night (any day)
        if hour_of_day >= 22 or hour_of_day <= 5:
            raw_scores["Local Residents"] *= 1.4
            raw_scores["Food Visitors"] *= 1.2
            raw_scores["Retail Shoppers"] *= 0.5
            raw_scores["Office Commuters"] *= 0.2
            raw_scores["Students"] *= 0.4

        # MODIFIER 2 — Trends Score
        if trends_score >= 75:
            raw_scores["Retail Shoppers"] *= 1.3
            raw_scores["Food Visitors"] *= 1.2
        elif trends_score <= 25:
            raw_scores["Local Residents"] *= 1.2
            raw_scores["Office Commuters"] *= 1.1

        # MODIFIER 3 — Weather Score
        if weather_score >= 70:
            raw_scores["Retail Shoppers"] *= 1.2
            raw_scores["Food Visitors"] *= 1.15
            raw_scores["Local Residents"] *= 1.1
        elif weather_score <= 30:
            raw_scores["Local Residents"] *= 1.3
            raw_scores["Food Visitors"] *= 1.2
            raw_scores["Retail Shoppers"] *= 0.8
            raw_scores["Office Commuters"] *= 0.9

        # MODIFIER 4 — Keyword Context Boost
        kw_lower = [k.lower() for k in keywords]
        
        if any(w in " ".join(kw_lower) for w in ["food", "coffee", "cafe", "restaurant", "eat", "lunch", "dinner", "brunch"]):
            raw_scores["Food Visitors"] *= 1.3
        if any(w in " ".join(kw_lower) for w in ["shop", "sale", "fashion", "clothing", "buy", "store", "mall"]):
            raw_scores["Retail Shoppers"] *= 1.3
        if any(w in " ".join(kw_lower) for w in ["gym", "fitness", "workout", "yoga", "health"]):
            raw_scores["Local Residents"] *= 1.3
        if any(w in " ".join(kw_lower) for w in ["school", "university", "study", "campus", "student"]):
            raw_scores["Students"] *= 1.3
        if any(w in " ".join(kw_lower) for w in ["office", "work", "business", "meeting", "coworking"]):
            raw_scores["Office Commuters"] *= 1.3

        # 3. Normalization
        total_score = sum(raw_scores.values())
        if total_score == 0:
            return [{"type": "Mixed Transit", "pct": 100, "desc": "Balanced distribution detected — insufficient POI density for specific persona targeting."}]

        # Initial normalization
        results = []
        for cat, score in raw_scores.items():
            pct = (score / total_score) * 100
            results.append({"type": cat, "raw_pct": pct})

        # Remove < 5% and re-normalize
        filtered_results = [r for r in results if r["raw_pct"] >= 5]
        if not filtered_results:
             return [{"type": "Mixed Transit", "pct": 100, "desc": "Balanced distribution detected — insufficient POI density for specific persona targeting."}]
             
        final_total = sum(r["raw_pct"] for r in filtered_results)
        final_output = []
        
        for r in filtered_results:
            pct = int(round((r["raw_pct"] / final_total) * 100))
            
            # 4. Generate Signal-Aware Descriptions
            desc = ""
            if r["type"] == "Food Visitors":
                if trends_score > 60 and (17 <= hour_of_day <= 21 or 11 <= hour_of_day <= 14):
                    desc = f"Strong dining intent detected — peak hour search activity and timing align for F&B campaigns. Heat score {heat_score:.0f} confirmed."
                else:
                    desc = f"Active food & beverage signal in this zone. Heat score of {heat_score:.0f} suggests stable dining intent."
            elif r["type"] == "Retail Shoppers":
                if not is_weekday and weather_score > 60:
                    desc = "Weekend foot traffic with favourable weather — high commercial conversion window."
                else:
                    desc = "Retail-focused audience detected. Signal strength suggests prime commercial targeting window."
            elif r["type"] == "Office Commuters":
                if is_weekday and 7 <= hour_of_day <= 10:
                    desc = "Morning commuter surge — professional audience active in this zone."
                else:
                    desc = "Professional/Office audience detected in nearby commercial clusters."
            elif r["type"] == "Local Residents":
                if weather_score < 40:
                    desc = "Reduced outdoor mobility — residential audience likely in near-home discovery mode."
                else:
                    desc = "High density of local residential activity. Effective for community-focused outreach."
            elif r["type"] == "Students":
                if trends_score > 60:
                    desc = "Academic cluster with elevated search activity — value-driven messaging recommended."
                else:
                    desc = "Concentrated youth and education-related transit detected nearby."

            final_output.append({
                "type": r["type"],
                "pct": pct,
                "desc": desc
            })

        # Final sort and return
        return sorted(final_output, key=lambda x: x["pct"], reverse=True)

    def _generate_radar_feed(
        self,
        keywords: List[str],
        trends_score: float,
        places_score: float,
        weather_score: float,
        place_types: List[str],
        radius: int
    ) -> List[Dict[str, Any]]:
        """Generate high-fidelity radar notifications from real signal state."""
        import uuid
        feed = []
        now = datetime.utcnow()
        
        # 1. Base Scan Log
        feed.append({
            "id": str(uuid.uuid4())[:8],
            "time": now.strftime("%H:%M:%S"),
            "msg": f"Satellite sweep complete: {radius/1000:.1f}KM radius locked",
            "type": "info"
        })
        
        # 2. Trends Signal
        if trends_score > 0.6:
            feed.append({
                "id": str(uuid.uuid4())[:8],
                "time": now.strftime("%H:%M:%S"),
                "msg": f"Digital intent surge detected for '{keywords[0]}'",
                "type": "alert"
            })
        
        # 3. Weather Signal
        if weather_score > 0.7:
            feed.append({
                "id": str(uuid.uuid4())[:8],
                "time": now.strftime("%H:%M:%S"),
                "msg": "Weather conditions favor high customer receptivity",
                "type": "success"
            })
        elif weather_score < 0.3:
             feed.append({
                "id": str(uuid.uuid4())[:8],
                "time": now.strftime("%H:%M:%S"),
                "msg": "External conditions suggest indoor-focused engagement",
                "type": "info"
            })

        # 4. Places / Crowd Signal
        if places_score > 0.6:
             feed.append({
                "id": str(uuid.uuid4())[:8],
                "time": now.strftime("%H:%M:%S"),
                "msg": f"High commercial density confirmed via {len(set(place_types))} nearby markers",
                "type": "success"
            })
        
        return feed

    # -----------------------------------------------------------------------
    # Heatmap
    # -----------------------------------------------------------------------

    async def get_heatmap(self, business_id: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Fetch recent heat scores and return as GeoJSON Feature dicts.
        """
        query = HeatScoreModel.find(
            HeatScoreModel.business_id == business_id
            if business_id
            else {}
        ).sort(-HeatScoreModel.timestamp).limit(limit)

        records = await query.to_list()
        features = []
        for rec in records:
            coords = rec.location.get("coordinates", [0.0, 0.0])
            features.append({
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": coords},
                "properties": {
                    "score": rec.score,
                    "urgency": rec.urgency,
                    "zone": rec.zone,
                    "timestamp": rec.timestamp.isoformat(),
                },
            })
        return features

    # -----------------------------------------------------------------------
    # Campaign History
    # -----------------------------------------------------------------------

    async def get_campaign_history(
        self,
        business_id: str,
        limit: int = 50,
    ) -> List[Dict]:
        """
        Return campaign log records for a given business, newest-first.
        """
        records = (
            await CampaignLogModel.find(
                CampaignLogModel.business_id == business_id
            )
            .sort(-CampaignLogModel.timestamp)
            .limit(limit)
            .to_list()
        )
        return [
            {
                "business_id": r.business_id,
                "keywords": r.keywords,
                "radius": r.radius,
                "final_score": r.final_score,
                "urgency": r.urgency,
                "is_indoor": r.is_indoor,
                "signals": r.signals,
                "timestamp": r.timestamp,
            }
            for r in records
        ]

    # -----------------------------------------------------------------------
    # Campaign Brief Persistence & Retrieval (v2)
    # -----------------------------------------------------------------------

    async def persist_strategic_brief(self, brief_data: Dict[str, Any]) -> str:
        """
        Store a fully assembled strategic brief in MongoDB.
        Returns the generated campaign ID.
        """
        try:
            # Add metadata if not present
            if "ai_model" not in brief_data:
                brief_data["ai_model"] = "gemini-1.5-flash"
            
            brief = CampaignBriefModel(**brief_data)
            await brief.insert()
            
            logger.info(
                "✅ Strategic brief persisted: business_id=%s id=%s",
                brief.business_id, 
                str(brief.id)
            )
            return str(brief.id)
        except Exception as exc:
            logger.error("❌ Failed to persist strategic brief: %s", exc, exc_info=True)
            # We don't raise here to avoid breaking the frontend response
            return "error_persistence_failed"

    async def get_brief_by_id(self, brief_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single campaign brief by its hex ID string."""
        from beanie import PydanticObjectId
        try:
            obj_id = PydanticObjectId(brief_id)
            brief = await CampaignBriefModel.get(obj_id)
            if not brief:
                return None
            data = brief.model_dump()
            # Make JSON-safe
            data["id"] = str(brief.id)
            data["campaign_id"] = str(brief.id)
            if "timestamp" in data and hasattr(data["timestamp"], "isoformat"):
                data["timestamp"] = data["timestamp"].isoformat()
            return data
        except Exception as e:
            logger.error(f"Error fetching brief {brief_id}: {e}")
            return None

    async def get_brief_history(
        self,
        business_id: str,
        user_email: Optional[str] = None,
        limit: int = 20,
        days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Retrieve recent campaign briefs for a business (and optionally a user) with time filtering."""
        from datetime import datetime, timedelta
        
        start_date = datetime.utcnow() - timedelta(days=days)

        filters = [
            CampaignBriefModel.business_id == business_id,
            CampaignBriefModel.timestamp >= start_date,
        ]
        if user_email:
            filters.append(CampaignBriefModel.user_email == user_email)

        query = CampaignBriefModel.find(*filters).sort(-CampaignBriefModel.timestamp).limit(limit)
        
        records = await query.to_list()
        result = []
        for r in records:
            data = r.model_dump()
            data["campaign_id"] = str(r.id)
            data["id"] = str(r.id)
            if "timestamp" in data and hasattr(data["timestamp"], "isoformat"):
                data["timestamp"] = data["timestamp"].isoformat()
            result.append(data)
        return result

    # -----------------------------------------------------------------------
    # Private persistence helpers
    # -----------------------------------------------------------------------

    async def _persist_campaign_log(
        self,
        business_id: str,
        keywords: List[str],
        location: Dict,
        radius: int,
        signals: Dict[str, float],
        final_score: int,
        urgency: str,
        is_indoor: bool,
        timestamp: datetime,
    ) -> None:
        """Insert a campaign_logs document — failure is logged but never bubbles up."""
        try:
            log = CampaignLogModel(
                business_id=business_id,
                keywords=keywords,
                location=location,
                radius=radius,
                signals=signals,
                final_score=final_score,
                urgency=urgency,
                is_indoor=is_indoor,
                timestamp=timestamp,
            )
            await log.insert()
        except Exception as exc:
            logger.error(
                "Failed to persist campaign log for business_id=%s: %s",
                business_id,
                exc,
            )

    async def _persist_heat_score(
        self,
        business_id: str,
        location: Dict,
        score: int,
        urgency: str,
        signals: Dict[str, float],
        radius: int,
        is_critical: bool,
        timestamp: datetime,
    ) -> None:
        """Insert a heat_scores document — failure is logged but never bubbles up."""
        try:
            hs = HeatScoreModel(
                business_id=business_id,
                location=location,
                score=score,
                urgency=urgency,
                zone="geo_intent",
                signals=signals,
                radius=radius,
                is_critical=is_critical,
                timestamp=timestamp,
            )
            await hs.insert()
        except Exception as exc:
            logger.error(
                "Failed to persist heat score for business_id=%s: %s",
                business_id,
                exc,
            )
