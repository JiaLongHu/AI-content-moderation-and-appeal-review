import pytest
from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def create_pending_post(client: TestClient) -> int:
    use_results(client, result(RiskLevel.L2, 1.0))
    response = client.post(
        "/api/v1/posts",
        json={"title": "待审核帖子", "body": "需要人工判断的内容"},
        headers=auth_headers(client),
    )
    assert response.json()["status"] == "pending_manual_review"
    return response.json()["id"]


def test_content_reviewer_can_publish_l2_task(client: TestClient) -> None:
    content_id = create_pending_post(client)
    reviewer_headers = auth_headers(client, "content_reviewer")
    tasks = client.get("/api/v1/moderation/tasks", headers=reviewer_headers)
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1
    task_id = tasks.json()[0]["id"]

    detail = client.get(f"/api/v1/moderation/tasks/{task_id}", headers=reviewer_headers)
    assert detail.json()["content_id"] == content_id
    assert detail.json()["moderation"]["final_level"] == "L2"

    decided = client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json={"final_category": "normal", "final_level": "L0", "decision": "publish"},
        headers=reviewer_headers,
    )
    assert decided.status_code == 200
    assert decided.json()["content_status"] == "published"
    assert client.get("/api/v1/moderation/tasks", headers=reviewer_headers).json() == []
    public_ids = [item["id"] for item in client.get(
        "/api/v1/posts", headers=auth_headers(client)
    ).json()]
    assert content_id in public_ids

    repeated = client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json={"final_category": "normal", "final_level": "L0", "decision": "publish"},
        headers=reviewer_headers,
    )
    assert repeated.status_code == 409


def test_content_reviewer_can_reject_l2_task(client: TestClient) -> None:
    content_id = create_pending_post(client)
    reviewer_headers = auth_headers(client, "content_reviewer")
    task_id = client.get("/api/v1/moderation/tasks", headers=reviewer_headers).json()[0]["id"]
    response = client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json={"final_category": "harassment", "final_level": "L3", "decision": "reject"},
        headers=reviewer_headers,
    )
    assert response.status_code == 200
    assert response.json()["content_status"] == "rejected"
    mine = client.get("/api/v1/me/contents", headers=auth_headers(client)).json()
    assert next(item for item in mine if item["id"] == content_id)["status"] == "rejected"


@pytest.mark.parametrize(
    "payload",
    [
        {"final_category": "normal", "final_level": "L2", "decision": "publish"},
        {"final_category": "harassment", "final_level": "L3", "decision": "publish"},
        {"final_category": "normal", "final_level": "L0", "decision": "reject"},
    ],
)
def test_illegal_manual_decisions_are_rejected(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    create_pending_post(client)
    headers = auth_headers(client, "content_reviewer")
    task_id = client.get("/api/v1/moderation/tasks", headers=headers).json()[0]["id"]
    assert client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json=payload,
        headers=headers,
    ).status_code == 422


def test_only_content_reviewer_can_access_tasks(client: TestClient) -> None:
    create_pending_post(client)
    assert client.get(
        "/api/v1/moderation/tasks", headers=auth_headers(client)
    ).status_code == 403
    assert client.get(
        "/api/v1/moderation/tasks", headers=auth_headers(client, "appeal_reviewer")
    ).status_code == 403


def test_comment_task_contains_only_minimum_context(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L0, 0.95),
        result(RiskLevel.L2, 1.0),
        result(RiskLevel.L2, 1.0),
    )
    post_id = client.post(
        "/api/v1/posts",
        json={"title": "上下文主题", "body": "上下文正文"},
        headers=auth_headers(client),
    ).json()["id"]
    client.post(
        f"/api/v1/posts/{post_id}/comments",
        json={"body": "需要结合上文"},
        headers=auth_headers(client),
    )
    headers = auth_headers(client, "content_reviewer")
    task_id = client.get("/api/v1/moderation/tasks", headers=headers).json()[0]["id"]
    detail = client.get(f"/api/v1/moderation/tasks/{task_id}", headers=headers).json()
    assert "上下文主题" in detail["context"]
    assert "上下文正文" in detail["context"]
    assert "完整评论区" not in detail["context"]
