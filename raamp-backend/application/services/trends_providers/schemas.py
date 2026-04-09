from __future__ import annotations

from pydantic import BaseModel, Field, RootModel
from typing import Any, Dict, List


class TrendsSearchInterest(BaseModel):
    """
    Canonical time-series contract for all trends providers.

    - `dates`: list of date-like strings (ISO preferred) aligned with every series in `data`
    - `data`: mapping keyword/series_name -> list of numeric values (same length as `dates`)
    """

    dates: List[str] = Field(default_factory=list)
    data: Dict[str, List[float]] = Field(default_factory=dict)


class TrendsProviderNormalizedPayload(BaseModel):
    """
    Canonical payload every provider must produce (success path).
    All fields must be present; missing data must default to empty collections.
    """

    search_interest: TrendsSearchInterest = Field(default_factory=TrendsSearchInterest)
    geo_data: Dict[str, Any] = Field(default_factory=dict)
    related_queries: "TrendsRelatedQueries" = Field(default_factory=lambda: TrendsRelatedQueries({}))
    rising_queries: "TrendsRisingQueries" = Field(default_factory=lambda: TrendsRisingQueries({}))


class TrendsQueryItem(BaseModel):
    """
    Canonical related/rising query item.
    Mirrors the shape returned by pytrends (query + value), and is a stable target
    for SerpAPI normalization.
    """

    query: str
    value: int = 0


class TrendsRelatedQueries(RootModel[Dict[str, List[TrendsQueryItem]]]):
    """
    Canonical related-queries container: keyword -> list[TrendsQueryItem]
    """

    root: Dict[str, List[TrendsQueryItem]] = Field(default_factory=dict)


class TrendsRisingQueries(RootModel[Dict[str, List[TrendsQueryItem]]]):
    """
    Canonical rising-queries container: keyword -> list[TrendsQueryItem]
    """

    root: Dict[str, List[TrendsQueryItem]] = Field(default_factory=dict)

