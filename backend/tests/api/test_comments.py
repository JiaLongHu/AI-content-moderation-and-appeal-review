from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def create_published_post(client: TestClient) -> int:
    response = client.post(
        "/api/v1/posts",
        json={"title": "讨论主题", "body": "一起聊聊这件事"},
        headers=auth_headers(client),
    )
    return response.json()["id"]


def test_comment_and_one_level_reply_are_published(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L0, 0.95),
    )
    post_id = create_published_post(client)
    comment = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "我也很感兴趣"},
        headers=auth_headers(client, "user_b"),
    )
    assert comment.status_code == 201
    comment_id = comment.json()["id"]
    reply = client.post(
        f"/api/v1/comments/{comment_id}/replies",
        json={"body": "那就一起参加吧"},
        headers=auth_headers(client),
    )
    assert reply.status_code == 201

    detail = client.get(f"/api/v1/posts/{post_id}", headers=auth_headers(client)).json()
    assert detail["comments"][0]["body"] == "我也很感兴趣"
    assert detail["comments"][0]["replies"][0]["body"] == "那就一起参加吧"
    assert "status" not in detail["comments"][0]


def test_uncertain_comment_retries_with_minimum_context(client: TestClient) -> None:
    reviewer = use_results(
        client,
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L2, 1.0),
        result(RiskLevel.L0, 0.90),
    )
    post_id = create_published_post(client)
    response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "这句话需要结合上文"},
        headers=auth_headers(client),
    )
    assert response.json()["status"] == "published"
    assert reviewer.calls[1] == ("这句话需要结合上文", None)
    assert "所属帖子标题" in (reviewer.calls[2][1] or "")
    assert "完整评论区" not in (reviewer.calls[2][1] or "")


def test_unpublished_parent_and_nested_reply_are_blocked(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L1, 0.79),
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L0, 0.95),
    )
    pending_post = client.post(
        "/api/v1/posts",
        json={"title": "待审核", "body": "尚不可评论"},
        headers=auth_headers(client),
    ).json()
    blocked_comment = client.post(
        f"/api/v1/posts/{pending_post['id']}/comments",
        json={"body": "不应成功"},
        headers=auth_headers(client),
    )
    assert blocked_comment.status_code == 409

    published_post = create_published_post(client)
    comment_id = client.post(
        f"/api/v1/posts/{published_post}/comments",
        json={"body": "一级评论"},
        headers=auth_headers(client),
    ).json()["id"]
    reply_id = client.post(
        f"/api/v1/comments/{comment_id}/replies",
        json={"body": "一层回复"},
        headers=auth_headers(client),
    ).json()["id"]
    nested = client.post(
        f"/api/v1/comments/{reply_id}/replies",
        json={"body": "禁止二层回复"},
        headers=auth_headers(client),
    )
    assert nested.status_code == 409


def test_comment_length_is_limited(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L0, 0.95))
    post_id = create_published_post(client)
    response = client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "x" * 501},
        headers=auth_headers(client),
    )
    assert response.status_code == 422
