import types

import pytest

from application.services.create_pack_service import CreatePackService


class _FakeUseCase:
    async def generate_social_content(self, *, user_id: str, campaign_idea: str, platform_type: str, content_type: str):
        # Return a predictable shape matching ContentGenerationUseCase output (dict-like)
        return {
            "success": True,
            "platform_type": platform_type,
            "generated_at": "now",
            "best_caption_id": 1,
            "caption_variants": [
                {"id": 1, "tone": "default", "caption": f"{platform_type}:{campaign_idea[:10]}", "hashtags": ["#a", "#b"]},
            ],
            "hashtag_sets": [{"id": 1, "hashtags": ["#a", "#b"]}],
        }


class _InMemoryDraft:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.id = "draft"

    async def insert(self):
        return self


@pytest.mark.asyncio
async def test_create_pack_creates_three_drafts(monkeypatch):
    # Patch CampaignDraftModel constructor used inside service
    from application import services as _services_pkg  # noqa: F401
    import application.services.create_pack_service as mod

    created = []

    def _factory(**kwargs):
        d = _InMemoryDraft(**kwargs)
        created.append(d)
        return d

    monkeypatch.setattr(mod, "CampaignDraftModel", _factory)

    svc = CreatePackService(content_use_case=_FakeUseCase())
    res = await svc.create_pack(
        user_id="u@example.com",
        trend_keyword="rr vs mi",
        niche="food",
        location="PK",
        suggested_hashtags=["#x"],
        suggested_caption="seed",
        platform="instagram",
    )

    assert len(res) == 3
    kinds = sorted([d.kind for d in created])
    assert kinds == ["carousel", "reel", "story"]
    assert all(d.user_id == "u@example.com" for d in created)
    assert all(isinstance(d.content, dict) for d in created)
    assert all("best_caption" in d.content for d in created)

