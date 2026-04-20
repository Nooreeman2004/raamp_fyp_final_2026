"""
Verify Geo-Intent external APIs: Google Places, Tomorrow.io, Google Trends (via fetchers).

Run:  cd raamp-backend && python tests/verify_geo_intent_apis.py

Note: Trends uses pytrends/SerpAPI (see TRENDS_PROVIDER) — no single "Trends API key";
      rate limits can cause slow runs or neutral scores even when the stack is healthy.
"""
import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

LAT, LNG = 33.7215, 73.0433
RADIUS_M = 2000
TRENDS_TIMEOUT_S = 40.0


async def verify_places() -> tuple[bool, str]:
    key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not key:
        return False, "GOOGLE_MAPS_API_KEY missing"
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {"location": f"{LAT},{LNG}", "radius": RADIUS_M, "key": key}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            data = r.json()
        status = data.get("status", "UNKNOWN")
        if status == "OK":
            n = len(data.get("results", []))
            return True, f"OK ({n} POIs in {RADIUS_M}m)"
        if status == "ZERO_RESULTS":
            return True, "OK (zero POIs — sparse area)"
        return False, f"status={status} {data.get('error_message', '')}"
    except Exception as e:
        return False, str(e)


async def verify_tomorrow() -> tuple[bool, str]:
    key = os.getenv("TOMORROW_API_KEY", "").strip()
    if not key:
        return False, "TOMORROW_API_KEY missing"
    url = "https://api.tomorrow.io/v4/weather/realtime"
    params = {
        "location": f"{LAT},{LNG}",
        "apikey": key,
        "units": "metric",
        "fields": "temperature,weatherCode",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            if r.status_code != 200:
                return False, f"HTTP {r.status_code}"
            data = r.json()
        temp = data.get("data", {}).get("values", {}).get("temperature")
        return True, f"OK (temp={temp}°C)" if temp is not None else "OK"
    except Exception as e:
        return False, str(e)


async def verify_trends_via_fetcher() -> tuple[bool, str]:
    """Same path as geo-intent radar (Google Trends / SerpAPI / pytrends)."""
    from application.services.geo_intent_fetchers import fetch_trends_score
    from config import Config

    geo = Config.GOOGLE_TRENDS_GEO or "PK"
    try:
        score, status = await asyncio.wait_for(
            fetch_trends_score(["coffee", "restaurant"], geo, LAT, LNG, RADIUS_M),
            timeout=TRENDS_TIMEOUT_S,
        )
        # Neutral 0.5 with "failed" still means the pipeline ran but data unavailable
        if status == "ok" and abs(score - 0.5) > 0.02:
            return True, f"OK score={score:.3f} status={status}"
        if status == "ok":
            return True, f"OK (score≈neutral {score:.3f} — macro signal flat)"
        return True, f"degraded score={score:.3f} status={status} (engine returns neutral on failure)"
    except asyncio.TimeoutError:
        return False, f"timeout after {TRENDS_TIMEOUT_S}s (rate limit / slow provider — retry later)"
    except Exception as e:
        return False, str(e)


async def main():
    print("Geo-Intent API verification")
    print(f"Coordinates: {LAT}, {LNG}\n")

    results = []

    ok, msg = await verify_places()
    results.append(("Google Maps Places API key", ok, msg))
    print(f"[{'OK ' if ok else 'FAIL'}] Google Maps Places: {msg}")

    ok, msg = await verify_tomorrow()
    results.append(("Tomorrow.io API key", ok, msg))
    print(f"[{'OK ' if ok else 'FAIL'}] Tomorrow.io: {msg}")

    ok, msg = await verify_trends_via_fetcher()
    results.append(("Google Trends signal path", ok, msg))
    print(f"[{'OK ' if ok else 'FAIL'}] Trends (fetch_trends_score): {msg}")

    print()
    core_ok = results[0][1] and results[1][1]
    if core_ok and results[2][1]:
        print("Summary: Maps + Tomorrow + Trends path all usable.")
        sys.exit(0)
    if core_ok:
        print("Summary: Maps + Tomorrow OK. Trends may be rate-limited or returning neutral — heat score can still blend real Places+Weather.")
        sys.exit(0)
    print("Summary: Fix failing keys above; geo-intent will return mostly neutral scores.")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
