from fastapi.testclient import TestClient

from backend.app.api.contents import get_moderation_service
from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation import ModerationService
from backend.app.moderation.schemas import CategoryScore, ModerationOutput
from backend.app.moderation.testing import StubAIReviewer
from backend.tests.conftest import TEST_PASSWORD


def result(level: RiskLevel, confidence: float) -> ModerationOutput:
    category = RiskCategory.NORMAL if level is RiskLevel.L0 else RiskCategory.HARASSMENT
    return ModerationOutput(
        categories=[CategoryScore(category=category, confidence=confidence)],
        final_category=category,
        final_level=level,
        reason="测试审核结果",
    )


def auth_headers(client: TestClient, username: str = "user_a") -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": TEST_PASSWORD},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def use_results(client: TestClient, *results: ModerationOutput) -> StubAIReviewer:
    reviewer = StubAIReviewer(*results)
    client.app.dependency_overrides[get_moderation_service] = lambda: ModerationService(reviewer)
    return reviewer


def test_published_post_is_public_without_moderation_metadata(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L0, 0.80))
    created = client.post(
        "/api/v1/posts",
        json={"title": "第一篇帖子", "body": "欢迎讨论周末活动"},
        headers=auth_headers(client),
    )
    assert created.status_code == 201
    assert created.json()["status"] == "published"

    posts = client.get("/api/v1/posts", headers=auth_headers(client, "user_b"))
    assert posts.status_code == 200
    assert posts.json()[0]["title"] == "第一篇帖子"
    assert "moderation" not in posts.json()[0]
    assert "status" not in posts.json()[0]


def test_l2_and_rejected_posts_are_only_visible_to_author(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L1, 0.79),
        result(RiskLevel.L3, 0.90),
    )
    headers = auth_headers(client)
    pending = client.post(
        "/api/v1/posts",
        json={"title": "待审核", "body": "边界内容"},
        headers=headers,
    )
    rejected = client.post(
        "/api/v1/posts",
        json={"title": "被拒绝", "body": "风险内容"},
        headers=headers,
    )
    assert pending.json()["status"] == "pending_manual_review"
    assert pending.json()["moderation"]["final_level"] == "L2"
    assert rejected.json()["status"] == "rejected"

    assert client.get("/api/v1/posts", headers=auth_headers(client, "user_b")).json() == []
    mine = client.get("/api/v1/me/contents", headers=headers).json()
    assert {item["status"] for item in mine} == {"pending_manual_review", "rejected"}
    assert client.get("/api/v1/me/contents", headers=auth_headers(client, "user_b")).json() == []


def test_post_validation_and_role_permissions(client: TestClient) -> None:
    headers = auth_headers(client)
    assert client.post(
        "/api/v1/posts",
        json={"title": " ", "body": "内容"},
        headers=headers,
    ).status_code == 422
    assert client.post(
        "/api/v1/posts",
        json={"title": "标题", "body": "x" * 3001},
        headers=headers,
    ).status_code == 422
    reviewer_headers = auth_headers(client, "content_reviewer")
    assert client.post(
        "/api/v1/posts",
        json={"title": "标题", "body": "内容"},
        headers=reviewer_headers,
    ).status_code == 403
