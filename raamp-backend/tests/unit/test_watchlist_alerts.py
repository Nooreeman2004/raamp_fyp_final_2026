import pytest


class _FakeWatchlistItem:
    def __init__(self):
        self.user_email = "u@example.com"
        self.keyword = "rr vs mi"
        self.is_active = True
        self.alert_on_spike = True
        self.velocity_threshold = 5.0
        self.alert_on_profit_score = True
        self.profit_score_threshold = 75.0
        self.alert_on_saturation_drop = True
        self.saturation_drop_threshold = 10.0
        self.last_saturation = 50.0
        self.last_velocity = 0.0
        self.last_arbitrage_score = 0.0
        self.last_profit_score = 0.0

    async def save(self):
        return self


class _FakeNotificationService:
    def __init__(self):
        self.sent = []

    async def create_and_send(self, **kwargs):
        self.sent.append(kwargs)
        return {"ok": True}


@pytest.mark.asyncio
async def test_watchlist_fires_spike_profit_and_saturation(monkeypatch):
    import application.services.trend_detection_service as mod
    from application.services.trend_detection_service import TrendDetectionService

    item = _FakeWatchlistItem()

    class _Finder:
        @staticmethod
        async def find_one(_q):
            return item

    monkeypatch.setattr(mod, "TrendWatchlistModel", _Finder)

    svc = TrendDetectionService()
    svc.notification_service = _FakeNotificationService()

    await svc._check_watchlist_alerts(
        user_email="u@example.com",
        keyword="rr vs mi",
        velocity=6.0,
        saturation=35.0,  # drop 15 from 50 -> fires
        profit_score=80.0,  # >= 75 -> fires
    )

    subtypes = sorted([n["metadata"].get("sub_type") for n in svc.notification_service.sent])
    assert "watchlist_alert" in subtypes
    assert "watchlist_profit_score" in subtypes
    assert "watchlist_saturation_drop" in subtypes

