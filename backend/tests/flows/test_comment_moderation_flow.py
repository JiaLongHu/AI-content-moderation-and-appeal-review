from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_only_published_comments_appear_in_post_detail(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L3, 0.90),
    )
    headers = auth_headers(client)
    post_id = client.post(
        "/api/v1/posts",
        json={"title": "主题", "body": "正文"},
        headers=headers,
    ).json()["id"]
    client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "公开评论"},
        headers=headers,
    )
    client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "拒绝评论"},
        headers=headers,
    )
    comments = client.get(f"/api/v1/posts/{post_id}", headers=headers).json()["comments"]
    assert [comment["body"] for comment in comments] == ["公开评论"]
