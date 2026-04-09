from application.services.trends_providers.schemas import TrendsRelatedQueries, TrendsRisingQueries


def test_related_queries_validation_accepts_canonical_shape():
    payload = {
        "fashion": [{"query": "summer outfit", "value": 100}, {"query": "linen pants", "value": 55}],
        "beauty": [{"query": "skin tint", "value": 12.0}],
    }
    TrendsRelatedQueries.model_validate(payload)


def test_rising_queries_validation_accepts_canonical_shape():
    payload = {
        "fashion": [{"query": "quiet luxury", "value": 999}],
    }
    TrendsRisingQueries.model_validate(payload)


def test_related_queries_validation_rejects_non_list_values():
    bad = {"fashion": {"top": [{"query": "x", "value": 1}]}}
    try:
        TrendsRelatedQueries.model_validate(bad)
        assert False, "expected validation error"
    except Exception:
        assert True

