# Application Layer - Trend Analytics Service
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from infrastructure.database.models.trend_detection_model import TrendDetectionModel
from infrastructure.database.models.trend_signal_model import TrendSignalModel
from application.services.trend_actionable_recommendation_service import TrendActionableRecommendationService

logger = logging.getLogger(__name__)

class TrendAnalyticsService:
    """Service for providing analytics data for trend dashboards"""

    @staticmethod
    def _norm_kw(s: Optional[str]) -> str:
        return (s or "").strip().lower()

    @staticmethod
    def _location_match_query(location: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Build a tolerant, case-insensitive Mongo query for location.

        Why:
        - Frontend often sends ISO2 codes (e.g., "PK")
        - DB records often store human names (e.g., "Pakistan") from onboarding/business profile
        - Older records may have mixed casing
        """
        loc = (location or "").strip()
        if not loc or loc.upper() == "GLOBAL":
            return None

        candidates: List[str] = [loc]

        # If loc looks like an ISO2 country code, try to also match the canonical country name.
        if len(loc) == 2 and loc.isalpha():
            try:
                from application.services.google_trends_service import GoogleTrendsService
                svc = GoogleTrendsService()
                # LOCATION_CODES is { "pakistan": "PK", ... }
                reverse = {str(v).upper(): str(k) for k, v in getattr(svc, "LOCATION_CODES", {}).items()}
                name_lower = reverse.get(loc.upper())
                if name_lower:
                    candidates.append(name_lower)           # "pakistan"
                    candidates.append(name_lower.title())   # "Pakistan"
            except Exception:
                # Best-effort only; still match the original loc below.
                pass

        # Use OR of case-insensitive exact matches.
        import re
        ors = []
        seen = set()
        for c in candidates:
            cc = (c or "").strip()
            if not cc:
                continue
            key = cc.lower()
            if key in seen:
                continue
            seen.add(key)
            ors.append({"location": {"$regex": f"^{re.escape(cc)}$", "$options": "i"}})

        if not ors:
            return None
        if len(ors) == 1:
            return ors[0]
        return {"$or": ors}

    @staticmethod
    def _signal_has_keyword(signal: TrendSignalModel, keyword: str) -> bool:
        kw = TrendAnalyticsService._norm_kw(keyword)
        if not kw:
            return False
        for k in (signal.keywords or []):
            if TrendAnalyticsService._norm_kw(str(k)) == kw:
                return True
        data = (signal.search_interest or {}).get("data") if isinstance(signal.search_interest, dict) else None
        if isinstance(data, dict):
            for k in data.keys():
                if TrendAnalyticsService._norm_kw(str(k)) == kw:
                    return True
        return False

    @staticmethod
    def _clamp01(x: float) -> float:
        try:
            return max(0.0, min(1.0, float(x)))
        except Exception:
            return 0.0

    @staticmethod
    def _clamp100(x: float) -> float:
        try:
            return max(0.0, min(100.0, float(x)))
        except Exception:
            return 0.0

    @staticmethod
    def _derive_profit_score(*, z_score: float, current_value: float, market_gap: float = 0.0) -> float:
        """
        Derive a 0..100 "opportunity" score when the pipeline didn't persist profit_score.

        Intuition:
        - Higher z_score => faster velocity spike (up to ~10)
        - Lower current_value => lower saturation/competition
        - market_gap (if available) nudges upward but is not required
        """
        z = max(0.0, float(z_score or 0.0))
        sat = TrendAnalyticsService._clamp100(float(current_value or 0.0))
        gap = max(0.0, float(market_gap or 0.0))

        z_component = min(60.0, z * 6.0)               # 0..60
        low_sat_component = min(35.0, (100.0 - sat) * 0.35)  # 0..35
        gap_component = min(5.0, gap * 5.0)            # 0..5  (gap is usually 0..1)

        return round(TrendAnalyticsService._clamp100(z_component + low_sat_component + gap_component), 2)

    @staticmethod
    def _fallback_recommendations(*, keyword: str, niche: str, location: str, profit_score: float, lifecycle_stage: str) -> Dict[str, Any]:
        """
        Deterministic, non-LLM fallback recommendations.
        Keeps the frontend "Actionable Strategy" section populated even without LLM keys.
        """
        kw = (keyword or "").strip()
        niche_norm = (niche or "general").strip()
        loc = (location or "GLOBAL").strip()
        stage = (lifecycle_stage or "Mainstream").strip()

        # Choose format based on stage and score.
        if stage.lower() in {"emerging", "breakout"} and profit_score >= 60:
            fmt = {"type": "reel", "goal": "Discovery", "reason": "Fast-moving trend: Reels capture early attention quickly."}
        elif stage.lower() in {"saturated", "declining"}:
            fmt = {"type": "carousel", "goal": "Trust", "reason": "Crowded topic: educational carousels help you stand out with value."}
        else:
            fmt = {"type": "carousel", "goal": "Discovery", "reason": "Balanced option: carousels drive saves/shares for consistent reach."}

        hooks = [
            f"Before you buy {kw}, check this…",
            f"The {kw} mistake most people in {loc} make",
            f"3 quick {kw} tips for {niche_norm} customers",
        ]
        content_ideas = [
            f"Reel: 20s myth vs fact about “{kw}” (end with a CTA to visit your page).",
            f"Carousel: 5 slides — what {kw} means + how it impacts {niche_norm} buyers in {loc}.",
            f"Story: poll + Q&A (“Are you into {kw} right now?”) then a limited-time offer/lead magnet.",
        ]
        hashtags = [
            f"#{kw.replace(' ', '')[:24]}",
            f"#{niche_norm.replace(' ', '')[:24]}",
            f"#{loc.replace(' ', '')[:24]}",
            "#Pakistan" if "pak" in loc.lower() else "#trending",
            "#smallbusiness",
        ]

        return {
            "campaign_suggestions": [
                f"Run a 48-hour promo around “{kw}” with a simple hook + limited-time offer.",
                f"Collaborate with a micro-creator in {loc} who already posts about {kw}.",
            ],
            "actionable_recommendations": {
                "content_format": fmt,
                "content_ideas": content_ideas,
                "hashtags": hashtags,
                "growth_hacks": [
                    "Post within the next 2 hours, then repost to Stories 6–8 hours later.",
                    "Ask a question in the caption and pin the best reply to drive comments.",
                ],
                "notes": "fallback_strategy (no LLM required)",
                "hooks": hooks,
            },
            "viral_audio": [],
        }

    async def get_live_feed(self, user_email: str, location: str = None, limit: int = 20, *, scope: str = "business") -> Dict[str, Any]:
        """Get the latest detected spikes for the user's live feed (with provenance metadata)"""
        from infrastructure.database.models.business_model import BusinessModel
        business = await BusinessModel.find_one({"user_id": user_email})
        current_niche = business.niche if business and hasattr(business, 'niche') else None
        specialties = list(getattr(business, "specialties", []) or []) if business else []
        specialties = [str(s).strip() for s in specialties if str(s).strip()]
        
        now = datetime.utcnow()
        query = {"user_id": user_email, "expires_at": {"$gt": now}, "status": {"$ne": "expired"}}
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)
        
        scope_norm = (scope or "business").strip().lower()

        # Filter by current niche to avoid showing stale trends from previous niches
        # IMPORTANT: Be tolerant to case/format drift (e.g., "Fashion" vs "fashion").
        # If this filter is too strict, it hides real detections and the UI falls back to a generic baseline card.
        if current_niche and scope_norm != "raw":
            try:
                import re
                query["niche"] = {"$regex": f"^{re.escape(str(current_niche))}$", "$options": "i"}
            except Exception:
                query["niche"] = str(current_niche)

        # Try to match detections with their parent TrendSignal...
        # However, for speed, we'll assume TrendSignalModel is the source of truth for "Live" high-level trends if we want social scores.
        # But TrendDetectionModel stores "Spikes".
        # Let's see if we can get the latest TrendSignal to augment.
        
        # NOTE: Ideally TrendDetectionModel should also store these scores at the spike level.
        # For now, let's keep the detections simple but if we have a matching TrendSignal, we could use it per keyword.
        # We can simulate social score if not present.
        
        # Fetch detections from database
        try:
            detections = await TrendDetectionModel.find(query).sort("-detected_at").limit(limit).to_list()
        except Exception as e:
            logger.error("Error fetching detections for %s: %s", user_email, str(e))
            detections = []

        # Soft fallback: if niche-filtered query returns nothing, retry without niche filter.
        # This prevents the UI from showing a non-actionable baseline ("all") when detections exist.
        if (not detections) and current_niche:
            try:
                query2 = dict(query)
                query2.pop("niche", None)
                detections = await TrendDetectionModel.find(query2).sort("-detected_at").limit(limit).to_list()
            except Exception:
                pass
        
        # --- Business relevance filter (keyword vs specialties) ---
        import re

        STOP = {"vs", "v", "and", "or", "the", "a", "an", "in", "of", "for", "to", "with", "on", "at", "by", "from", "today", "now", "live"}

        def tokenize(s: str) -> List[str]:
            raw = re.findall(r"[a-z0-9]+", (s or "").lower())
            out: List[str] = []
            for t in raw:
                if len(t) < 3:
                    continue
                if t in STOP:
                    continue
                out.append(t)
            return out

        business_tokens = set()
        if scope_norm != "raw":
            business_tokens.update(tokenize(str(current_niche or "")))
            for sp in specialties:
                business_tokens.update(tokenize(sp))

        results: List[Dict[str, Any]] = []
        for d in detections:
            try:
                z = float(d.z_score or 0.0)
                cur = float(d.current_value or 0.0)
                # TrendDetectionModel.market_gap is stored as 0..1-ish in practice; treat missing as 0.
                mg = float(getattr(d, "market_gap", 0.0) or 0.0)

                derived_profit = self._derive_profit_score(z_score=z, current_value=cur, market_gap=mg)
                profit_score = float(getattr(d, "profit_score", None) or derived_profit)
                lifecycle = getattr(d, 'lifecycle_stage', "Mainstream") or "Mainstream"

                recs = getattr(d, "recommendations", None)
                if not recs:
                    recs = self._fallback_recommendations(
                        keyword=str(d.keyword or ""),
                        niche=str(d.niche or ""),
                        location=str(d.location or ""),
                        profit_score=float(profit_score),
                        lifecycle_stage=str(lifecycle),
                    )

                # If scope=business, require at least some match to niche/specialties.
                # This prevents "scotland vs oman" from showing as a "fashion" spike unless it matches business tokens.
                if scope_norm != "raw" and business_tokens:
                    kw_tokens = set(tokenize(str(d.keyword or "")))
                    overlap = len(kw_tokens.intersection(business_tokens))
                    overlap_ratio = overlap / max(1, len(kw_tokens))
                    # Keep if:
                    # - at least 1 token overlaps, or
                    # - detection explicitly has niche_match_score >= 0.35
                    nms = float(getattr(d, "niche_match_score", 0.0) or 0.0)
                    if overlap == 0 and nms < 0.35:
                        continue

                results.append({
                    "id": str(d.id),
                    "keyword": d.keyword,
                    "niche": d.niche,
                    "location": d.location,
                    "score": round(d.z_score, 2) if d.z_score is not None else 0.0,
                    "z_score_spike": round(d.z_score, 2) if d.z_score is not None else 0.0,
                    "impact": d.impact_level,
                    "detected_at": d.detected_at,
                    "current_value": d.current_value,
                    "is_spike": True,
                    "sentiment": "POSITIVE" if (d.sentiment_score or 0) > 0 else "NEUTRAL",
                    "arbitrage_score": round(((d.z_score or 0) * 5) + (100 - (d.current_value or 50)) / 2, 2),
                    "profitability": round(((d.z_score or 0) * 5) + (100 - (d.current_value or 50)) / 2, 2),
                    "confidence": round(0.85 + (min(d.z_score or 0, 10)/50), 2),
                    "time_diff": "just now",
                    "social_score": float((d.z_score or 0) * 8),
                    "saturation_score": d.current_value or 50,
                    "is_real_social": bool(getattr(d, "is_real_social", False)),
                    "is_real_saturation": bool(getattr(d, "is_real_saturation", False)),
                    "is_real_events": bool(getattr(d, "is_real_events", False)),
                    "lifecycle_stage": lifecycle,
                    "predicted_growth_pct": getattr(d, 'predicted_growth_pct', 0.0) or 0.0,
                    "breakout_probability": getattr(d, 'breakout_probability', 0.0) or 0.0,
                    "profit_score": profit_score,
                    "timeframe": getattr(d, 'timeframe', "30d") or "30d",
                    "recommendations": recs,
                    # Data quality / provenance
                    "is_simulated": False,
                    "trend_signal_id": None,
                    "fetch_status": None,
                    "error_message": None,
                })
            except Exception as e:
                logger.warning("Error processing single detection record: %s", str(e))
                continue

        # Diagnostic: record which path served the live feed.
        live_feed_source: str = ""

        # Tighten enrichment: join to a recent TrendSignalModel by keyword + recency.
        # Only mark "real" if enrichment fields are populated and the signal is recent.
        if results:
            live_feed_source = f"real_signals ({len(results)} records)"
            now = datetime.utcnow()
            window_start = now - timedelta(hours=2)

            signal_query: Dict[str, Any] = {"user_email": user_email}
            locq2 = self._location_match_query(location)
            if locq2:
                signal_query.update(locq2)

            recent_signals = (
                await TrendSignalModel.find(signal_query)
                .sort("-created_at")
                .limit(20)
                .to_list()
            )

            # Keep only signals within the recency window.
            recent_signals = [s for s in recent_signals if getattr(s, "created_at", None) and s.created_at >= window_start]

            for r in results:
                kw = r.get("keyword", "")
                match = None
                for s in recent_signals:
                    if self._signal_has_keyword(s, kw):
                        match = s
                        break

                if not match:
                    continue

                r["trend_signal_id"] = str(match.id)
                r["fetch_status"] = match.fetch_status
                r["error_message"] = match.error_message

                # "Real" flags only if:
                # - signal claims it used real sources
                # - and the enriched metrics exist (not just defaults)
                if match.is_real_social and (match.social_score is not None) and (match.platform_bias is not None) and (len(match.platform_bias) > 0):
                    r["is_real_social"] = True
                if match.is_real_saturation and (match.saturation_score is not None):
                    r["is_real_saturation"] = True
                
                # Copy rising queries for title selection in frontend
                if match.rising_queries:
                    # rising_queries is a dict like {'top': [...], 'rising': [...]} in PyTrends
                    # or potentially a flat list in SerpAPI mode.
                    if isinstance(match.rising_queries, dict):
                        q_data = match.rising_queries.get("rising", []) or match.rising_queries.get("top", [])
                        if isinstance(q_data, list):
                            r["rising_queries"] = [str(q) for q in q_data[:5]]
                    elif isinstance(match.rising_queries, list):
                        r["rising_queries"] = [str(q) for q in match.rising_queries[:5]]

        # If no spikes, show "Baseline Trends" from TrendSignal (Layer 1 Source)
        if not results:
            signal_query = {"user_email": user_email, "fetch_status": "completed"}
            locq3 = self._location_match_query(location)
            if locq3:
                signal_query.update(locq3)
            
            latest_signal = await TrendSignalModel.find(signal_query).sort("-created_at").first_or_none()
            
            # Fail-closed: if no completed signal exists, return an empty feed (no synthetic baseline).
            if not latest_signal:
                logger.info("live_feed_source: real_signals (0 records)")
                return {
                    "trends": [],
                    "data_quality": {
                        "is_real": False,
                        "source": "empty_no_detections_no_completed_signal",
                        "notes": "No detections yet. Run a scan to populate the live feed.",
                        "flags": {"is_real_social": False, "is_real_saturation": False, "is_real_events": False},
                    },
                }
            
            elif latest_signal and latest_signal.keywords:
                # Create baseline trends from the signal's keywords
                logger.info("No spikes found, creating baseline trends from signal %s", str(latest_signal.id))
                live_feed_source = "real_signals (baseline_from_completed_signal)"
                
                # Choose a stable, non-generic keyword for the primary card.
                primary_kw = None
                niche_norm = self._norm_kw(str(getattr(latest_signal, "niche", "") or ""))
                for k in (latest_signal.keywords or []):
                    kk = str(k or "").strip()
                    if not kk:
                        continue
                    kkn = kk.lower()
                    if kkn == "all":
                        continue
                    # Avoid showing niche as the "trend keyword" if it leaked into keywords list
                    if niche_norm and self._norm_kw(kk) == niche_norm:
                        continue
                    primary_kw = kk
                    break
                if not primary_kw:
                    primary_kw = str((latest_signal.keywords or ["trend"])[0])

                # Do NOT generate recommendations at read-time for baseline cards.
                # Recommendations are generated and persisted on TrendDetectionModel during the scan pipeline.
                rec_payload = None

                # Main trend from enriched data
                results.append({
                    "id": str(latest_signal.id),
                    "keyword": primary_kw,
                    "niche": latest_signal.niche,
                    "location": latest_signal.location,
                    "score": round(latest_signal.arbitrage_score / 10, 2) if latest_signal.arbitrage_score is not None else 0.0,
                    "z_score_spike": None,
                    "impact": "BASELINE",
                    "rising_queries": (latest_signal.rising_queries.get("rising", []) or latest_signal.rising_queries.get("top", [])) if isinstance(latest_signal.rising_queries, dict) else (latest_signal.rising_queries or []),
                    "detected_at": latest_signal.fetched_at or latest_signal.created_at,
                    "current_value": latest_signal.saturation_score,
                    "is_spike": False,
                    "label": "BASELINE",
                    "sentiment": "NEUTRAL",
                    "arbitrage_score": latest_signal.arbitrage_score,
                    "profitability": latest_signal.arbitrage_score,
                    "confidence": None,
                    "time_diff": "just now",
                    "social_score": latest_signal.social_score,
                    "saturation_score": latest_signal.saturation_score,
                    "hashtags": latest_signal.hashtags[:3] if latest_signal.hashtags else [],
                    "is_real_social": latest_signal.is_real_social,
                    "is_real_saturation": latest_signal.is_real_saturation,
                    "is_real_events": bool(getattr(latest_signal, "is_real_events", False)),
                    "lifecycle_stage": latest_signal.lifecycle_stage or "Mainstream",
                    "predicted_growth_pct": latest_signal.predicted_growth_pct or 0.0,
                    "breakout_probability": latest_signal.breakout_probability or 0.0,
                    "profit_score": latest_signal.profit_score or 50.0,
                    "timeframe": latest_signal.timeframe or "30d",
                    "recommendations": rec_payload,
                    "is_simulated": False,
                    "trend_signal_id": str(latest_signal.id),
                    "fetch_status": latest_signal.fetch_status,
                    "error_message": latest_signal.error_message,
                })

                # Fail-closed: do not fabricate secondary baseline items from rising queries
                # using hardcoded saturation/social/arbitrage defaults.
                
                # Sort by score and limit
                results.sort(key=lambda x: x["score"] if isinstance(x["score"], (int, float)) else 0, reverse=True)
                results = results[:limit]
            else:
                logger.warning("No completed trend signals found for user %s", user_email)

        if live_feed_source:
            logger.info("live_feed_source: %s", live_feed_source)
        else:
            logger.info("live_feed_source: real_signals (%d records)", len(results))
        # Data quality:
        # - If we have actual detections, this is real persisted spike data.
        # - If we used baseline_from_completed_signal, this is real persisted scan data (not a spike).
        baseline_used = "baseline_from_completed_signal" in (live_feed_source or "")
        is_real = bool(results)
        source = "trend_detections" if not baseline_used else "trend_signals.baseline"

        # Standardize provenance flags in data_quality.flags for UI + monitoring.
        any_real_social = any(bool(t.get("is_real_social")) for t in results)
        any_real_saturation = any(bool(t.get("is_real_saturation")) for t in results)
        any_real_events = any(bool(t.get("is_real_events")) for t in results)
        flags = {
            "baseline_used": baseline_used,
            "live_feed_source": live_feed_source or "",
            "is_real_social": any_real_social,
            "is_real_saturation": any_real_saturation,
            "is_real_events": any_real_events,
        }
        return {
            "trends": results,
            "data_quality": {
                "is_real": is_real,
                "source": source,
                "notes": "Baseline shown (no spikes detected yet)." if baseline_used else None,
                "flags": flags,
            },
        }

    async def get_geo_heatmap(self, user_email: str, location: str = None) -> List[Dict[str, Any]]:
        """Get geographic intensity data with coordinates for map visualization"""
        from infrastructure.database.models.business_model import BusinessModel
        business = await BusinessModel.find_one({"user_id": user_email})
        current_niche = business.niche if business and hasattr(business, 'niche') else None

        query = {"user_email": user_email}
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)
            
        if current_niche:
            query["niche"] = current_niche

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
            # Fail-closed: no synthetic geo-intensity.
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
        from infrastructure.database.models.business_model import BusinessModel
        business = await BusinessModel.find_one({"user_id": user_email})
        current_niche = business.niche if business and hasattr(business, 'niche') else None

        start_date = datetime.utcnow() - timedelta(days=days)
        now = datetime.utcnow()
        query = {
            "user_id": user_email,
            "detected_at": {"$gte": start_date},
            "expires_at": {"$gt": now},
            "status": {"$ne": "expired"},
        }
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)
            
        if current_niche:
            query["niche"] = current_niche

        detections = await TrendDetectionModel.find(query).sort("detected_at").to_list()
        
        # Group by date
        timeline = {}
        for d in detections:
            try:
                # Ensure detected_at has a value for strftime
                dt = d.detected_at or d.created_at or datetime.utcnow()
                date_str = dt.strftime("%Y-%m-%d")
                if date_str not in timeline:
                    timeline[date_str] = {"date": date_str, "count": 0, "avg_z": 0.0}
                timeline[date_str]["count"] += 1
                timeline[date_str]["avg_z"] += (d.z_score or 0.0)
            except Exception as e:
                logger.warning("Error processing timeline entry: %s", str(e))
                continue
            
        # Finalize averages
        for date in timeline:
            timeline[date]["avg_z"] = round(timeline[date]["avg_z"] / timeline[date]["count"], 2)

        if not timeline:
            logger.info(
                "📈 SPIKE TIMELINE - No detections in window for %s (empty chart; no synthetic fill)",
                user_email,
            )

        return sorted(list(timeline.values()), key=lambda x: x["date"])

    async def get_last_successful_scan_at(
        self, user_email: str, location: str = None
    ) -> Optional[datetime]:
        """UTC timestamp of the most recent completed trend fetch for this scope."""
        query: Dict[str, Any] = {"user_email": user_email, "fetch_status": "completed"}
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)

        sig = await TrendSignalModel.find(query).sort("-updated_at").first_or_none()
        if not sig:
            return None
        return sig.fetched_at or sig.updated_at

    async def get_market_gap_data(self, user_email: str, location: str = None) -> List[Dict[str, Any]]:
        """
        Get data for the Sweet Spot Matrix (Saturation vs Velocity).
        X-axis: Saturation (Current Value 0-100)
        Y-axis: Velocity (Z-Score)
        """
        from infrastructure.database.models.business_model import BusinessModel
        business = await BusinessModel.find_one({"user_id": user_email})
        current_niche = business.niche if business and hasattr(business, 'niche') else None
        
        now = datetime.utcnow()
        query = {"user_id": user_email, "expires_at": {"$gt": now}, "status": {"$ne": "expired"}}
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)
            
        if current_niche:
            query["niche"] = current_niche

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
                "is_real_social": bool(getattr(d, "is_real_social", False)),
                "is_real_saturation": bool(getattr(d, "is_real_saturation", False)),
                "is_real_events": bool(getattr(d, "is_real_events", False)),
            })

        # Enrichment flags
        if results:
            latest_signals = await TrendSignalModel.find({"user_email": user_email}).sort("-created_at").limit(10).to_list()
            signal_map = {s.keywords[0].lower(): s for s in latest_signals if s.keywords}
            for r in results:
                match = signal_map.get(r['keyword'].lower())
                if match:
                    r['is_real_social'] = match.is_real_social
                    r['is_real_saturation'] = match.is_real_saturation
                    r['is_real_events'] = bool(getattr(match, "is_real_events", False))

        # IMPORTANT: no synthetic bootstrap.
        # If there are not enough real detections yet, the UI should show an empty state.
        return results[:30]
    
    async def get_platform_reach(self, user_email: str, location: str = None) -> Dict[str, Any]:
        """
        Return platform split derived from persisted trend data.

        Source of truth:
        - `TrendSignalModel.platform_bias` (persisted by the trend pipeline).

        If bias is unavailable or not based on real social metrics, the response is gated with
        `is_real=False` and returns zeros (fail-closed vs guessing).
        """
        from infrastructure.database.models.business_model import BusinessModel
        business = await BusinessModel.find_one({"user_id": user_email})
        current_niche = business.niche if business and hasattr(business, 'niche') else None

        query: Dict[str, Any] = {"user_email": user_email}
        locq = self._location_match_query(location)
        if locq:
            query.update(locq)
            
        if current_niche:
            query["niche"] = current_niche
            
        latest_signal = (
            await TrendSignalModel.find(query)
            .sort("-created_at")
            .first_or_none()
        )

        if not latest_signal:
            return {
                "google": 0,
                "instagram": 0,
                "facebook": 0,
                "total_reach": "0%",
                "is_real": False,
                "source": "no_trend_signal",
            }

        bias = latest_signal.platform_bias if isinstance(latest_signal.platform_bias, dict) else {}
        # Treat as "real" only if pipeline explicitly marked it real and bias has non-zero content.
        bias_values = []
        for k in ("google", "instagram", "facebook"):
            try:
                v = float(bias.get(k, 0.0) or 0.0)
            except Exception:
                v = 0.0
            bias_values.append(max(0.0, v))

        total = sum(bias_values)
        is_real = bool(getattr(latest_signal, "is_real_social", False)) and total > 0.0

        if not is_real:
            return {
                "google": 0,
                "instagram": 0,
                "facebook": 0,
                "total_reach": "0%",
                "is_real": False,
                "source": "platform_bias_unavailable_or_not_real",
            }

        # Normalize into integer percents that sum to ~100.
        google_pct = int(round((bias_values[0] / total) * 100))
        instagram_pct = int(round((bias_values[1] / total) * 100))
        facebook_pct = int(round((bias_values[2] / total) * 100))

        # Fix rounding drift to ensure totals don't exceed 100.
        drift = (google_pct + instagram_pct + facebook_pct) - 100
        if drift != 0:
            # subtract drift from the largest bucket
            buckets = [("google", google_pct), ("instagram", instagram_pct), ("facebook", facebook_pct)]
            buckets.sort(key=lambda kv: kv[1], reverse=True)
            name, val = buckets[0]
            val = max(0, val - drift)
            if name == "google":
                google_pct = val
            elif name == "instagram":
                instagram_pct = val
            else:
                facebook_pct = val

        return {
            "google": google_pct,
            "instagram": instagram_pct,
            "facebook": facebook_pct,
            "total_reach": "100%",
            "is_real": True,
            "source": "trend_signal.platform_bias",
            "trend_signal_id": str(latest_signal.id),
        }
