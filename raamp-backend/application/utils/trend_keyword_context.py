import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class MatchupResolution:
    looks_like_matchup: bool
    matchup_hint: str
    entities: List[str]


_TEAM_MAP = {
    # IPL
    "rr": "Rajasthan Royals",
    "mi": "Mumbai Indians",
    "rcb": "Royal Challengers Bangalore",
    "csk": "Chennai Super Kings",
    "kkr": "Kolkata Knight Riders",
    "dc": "Delhi Capitals",
    "srh": "Sunrisers Hyderabad",
    "gt": "Gujarat Titans",
    "lsg": "Lucknow Super Giants",
    "pbks": "Punjab Kings",
    "kxip": "Punjab Kings",
    # countries (common sports shorthand)
    "pak": "Pakistan",
    "ind": "India",
}


def resolve_matchup(keyword: str) -> MatchupResolution:
    """
    Deterministically resolve simple "X vs Y" keywords into real entities.
    This is intentionally conservative: if we can't resolve confidently, we return empty hint/entities.
    """
    raw = (keyword or "").strip()
    if not raw:
        return MatchupResolution(False, "", [])

    lowered = raw.lower()
    looks_like = (" vs " in lowered) or (" v " in lowered)
    if not looks_like:
        return MatchupResolution(False, "", [])

    # normalize delimiter
    normalized = re.sub(r"\s+v\s+", " vs ", lowered, flags=re.IGNORECASE)
    parts = [p.strip() for p in normalized.split(" vs ") if p.strip()]
    if len(parts) < 2:
        return MatchupResolution(True, "", [])

    left, right = parts[0], parts[1]
    l = _TEAM_MAP.get(left, "")
    r = _TEAM_MAP.get(right, "")
    if not (l and r):
        return MatchupResolution(True, "", [])

    hint = f"{l} vs {r} (sports matchup)"
    return MatchupResolution(True, hint, [l, r])


def classify_keyword(keyword: str) -> Tuple[str, float]:
    """
    Lightweight keyword classifier for UI labels.
    Returns (category, confidence 0..1).

    Categories are intentionally broad: sports, news, brand, product, entertainment, generic.
    """
    text = (keyword or "").strip().lower()
    if not text:
        return ("generic", 0.0)

    matchup = resolve_matchup(text)
    if matchup.looks_like_matchup:
        # even unresolved matchups are likely sports chatter
        return ("sports", 0.85 if matchup.matchup_hint else 0.6)

    # News / macro signals
    if any(tok in text for tok in ["oil price", "oil prices", "inflation", "interest rate", "budget", "rupee", "dollar", "petrol", "diesel"]):
        return ("news", 0.7)

    # Entertainment / pop culture
    if any(tok in text for tok in ["trailer", "episode", "season", "netflix", "drama", "movie", "song", "lyrics"]):
        return ("entertainment", 0.65)

    # Product intent (very rough)
    if any(tok in text for tok in ["buy", "price", "review", "launch", "drop", "sale", "discount"]):
        return ("product", 0.55)

    return ("generic", 0.4)

