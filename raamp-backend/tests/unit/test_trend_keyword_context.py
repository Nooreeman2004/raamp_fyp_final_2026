import pytest


from application.utils.trend_keyword_context import resolve_matchup, classify_keyword


def test_resolve_matchup_rr_vs_mi():
    res = resolve_matchup("rr vs mi")
    assert res.looks_like_matchup is True
    assert res.matchup_hint == "Rajasthan Royals vs Mumbai Indians (sports matchup)"
    assert res.entities == ["Rajasthan Royals", "Mumbai Indians"]


def test_resolve_matchup_unresolved_still_matchup():
    res = resolve_matchup("abc vs xyz")
    assert res.looks_like_matchup is True
    assert res.matchup_hint == ""
    assert res.entities == []


def test_resolve_matchup_non_matchup():
    res = resolve_matchup("oil prices")
    assert res.looks_like_matchup is False
    assert res.matchup_hint == ""
    assert res.entities == []


@pytest.mark.parametrize(
    "kw,expected_category",
    [
        ("rr vs mi", "sports"),
        ("Oil prices on the rise", "news"),
        ("netflix trailer", "entertainment"),
        ("buy iphone price", "product"),
        ("some random thing", "generic"),
    ],
)
def test_classify_keyword_categories(kw, expected_category):
    category, conf = classify_keyword(kw)
    assert category == expected_category
    assert 0.0 <= conf <= 1.0

