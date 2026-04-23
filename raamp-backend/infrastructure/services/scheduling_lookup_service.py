"""
Platform Scheduling Recommendations
====================================
Static lookup tables for optimal posting times by platform and niche.
Based on published platform studies and industry best practices.
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class ScheduleWindow:
    """Optimal posting time window"""
    days: List[str]  # ["Tuesday", "Thursday"]
    time_range: str  # "6-8 PM"
    confidence: str  # "High", "Medium"
    source: str  # Research source


# Instagram Posting Schedule by Niche
INSTAGRAM_SCHEDULES: Dict[str, ScheduleWindow] = {
    "restaurant": ScheduleWindow(
        days=["Tuesday", "Wednesday", "Thursday"],
        time_range="11 AM - 1 PM, 7-9 PM",
        confidence="High",
        source="Hootsuite 2024 Restaurant Social Media Study"
    ),
    "food": ScheduleWindow(
        days=["Tuesday", "Thursday"],
        time_range="11 AM - 1 PM, 6-8 PM",
        confidence="High",
        source="Sprout Social 2024 Food & Beverage Report"
    ),
    "fitness": ScheduleWindow(
        days=["Tuesday", "Thursday"],
        time_range="6-8 PM",
        confidence="High",
        source="Later.com Fitness Industry Analysis 2024"
    ),
    "retail": ScheduleWindow(
        days=["Monday", "Wednesday", "Friday"],
        time_range="10 AM - 12 PM, 5-7 PM",
        confidence="Medium",
        source="Buffer State of Social 2024"
    ),
    "general": ScheduleWindow(
        days=["Wednesday", "Thursday"],
        time_range="11 AM - 1 PM",
        confidence="Medium",
        source="Meta for Business Best Practices 2024"
    ),
}

# TikTok Posting Schedule by Niche
TIKTOK_SCHEDULES: Dict[str, ScheduleWindow] = {
    "restaurant": ScheduleWindow(
        days=["Friday", "Saturday"],
        time_range="6-10 PM",
        confidence="High",
        source="TikTok Creator Portal - Food & Beverage Insights"
    ),
    "food": ScheduleWindow(
        days=["Wednesday", "Friday"],
        time_range="7-9 PM",
        confidence="High",
        source="Influencer Marketing Hub TikTok Study 2024"
    ),
    "fitness": ScheduleWindow(
        days=["Monday", "Wednesday", "Friday"],
        time_range="5-7 AM, 5-8 PM",
        confidence="High",
        source="TikTok Fitness Community Analysis"
    ),
    "retail": ScheduleWindow(
        days=["Thursday", "Friday"],
        time_range="7-9 PM",
        confidence="Medium",
        source="Hootsuite TikTok Best Times 2024"
    ),
    "general": ScheduleWindow(
        days=["Tuesday", "Thursday", "Saturday"],
        time_range="6-9 PM",
        confidence="Medium",
        source="Later.com TikTok Analytics Report"
    ),
}

# Facebook Posting Schedule by Niche
FACEBOOK_SCHEDULES: Dict[str, ScheduleWindow] = {
    "restaurant": ScheduleWindow(
        days=["Wednesday", "Friday"],
        time_range="12-1 PM, 5-6 PM",
        confidence="High",
        source="Meta Business Restaurants Guide 2024"
    ),
    "food": ScheduleWindow(
        days=["Thursday", "Friday"],
        time_range="1-3 PM",
        confidence="High",
        source="Sprout Social Facebook Engagement Report"
    ),
    "fitness": ScheduleWindow(
        days=["Monday", "Wednesday"],
        time_range="5-6 AM, 5-7 PM",
        confidence="Medium",
        source="CoSchedule Social Media Calendar Study"
    ),
    "retail": ScheduleWindow(
        days=["Wednesday", "Friday"],
        time_range="1-3 PM",
        confidence="Medium",
        source="Buffer Facebook Analytics 2024"
    ),
    "general": ScheduleWindow(
        days=["Wednesday", "Friday"],
        time_range="1-3 PM",
        confidence="Medium",
        source="Meta for Business Posting Guide"
    ),
}


def get_schedule_recommendation(platform: str, niche: str = "restaurant") -> ScheduleWindow:
    platform = platform.lower().strip()
    niche = niche.lower().strip()

    # Combined Instagram + Facebook: days that perform well on both platforms
    BOTH_SCHEDULES: Dict[str, ScheduleWindow] = {
        "restaurant": ScheduleWindow(
            days=["Wednesday", "Thursday"],
            time_range="12-1 PM, 7-9 PM",
            confidence="High",
            source="Combined: Meta Business & Hootsuite 2024 Restaurant Study"
        ),
        "food": ScheduleWindow(
            days=["Thursday", "Friday"],
            time_range="12-2 PM, 6-8 PM",
            confidence="High",
            source="Combined: Sprout Social Food & Beverage Reports"
        ),
        "fitness": ScheduleWindow(
            days=["Monday", "Wednesday"],
            time_range="5-7 AM, 5-8 PM",
            confidence="High",
            source="Combined: CoSchedule & Later.com Fitness Studies"
        ),
        "retail": ScheduleWindow(
            days=["Wednesday", "Friday"],
            time_range="12-2 PM, 5-7 PM",
            confidence="Medium",
            source="Combined: Buffer & Hootsuite Retail Reports"
        ),
        "general": ScheduleWindow(
            days=["Wednesday", "Friday"],
            time_range="12-2 PM, 5-7 PM",
            confidence="Medium",
            source="Combined: Meta for Business Best Practices"
        ),
    }

    platform_schedules = {
        "instagram": INSTAGRAM_SCHEDULES,
        "facebook": FACEBOOK_SCHEDULES,
        "tiktok": TIKTOK_SCHEDULES,
        "both": BOTH_SCHEDULES,
    }

    schedules = platform_schedules.get(platform, INSTAGRAM_SCHEDULES)
    return schedules.get(niche, schedules.get("general"))


def get_next_optimal_posting_time(platform: str, niche: str = "restaurant") -> Tuple[str, str]:
    """
    Get the next upcoming optimal posting day and time.
    
    Returns:
        Tuple of (day, time_range) e.g., ("Tuesday", "11 AM - 1 PM")
    """
    schedule = get_schedule_recommendation(platform, niche)
    
    # For now, return first recommended day and time
    # In production, this would calculate actual next occurrence
    return schedule.days[0], schedule.time_range.split(",")[0].strip()


# Platform minimum effective budgets (daily, in USD)
PLATFORM_MIN_BUDGETS: Dict[str, float] = {
    "instagram": 5.0,
    "facebook": 5.0,
    "tiktok": 50.0,  # TikTok has higher minimum for effective delivery
    "combined": 30.0,  # Instagram + TikTok
}


def get_min_budget(platform: str) -> float:
    """Get minimum effective daily budget for platform"""
    return PLATFORM_MIN_BUDGETS.get(platform.lower(), 10.0)
