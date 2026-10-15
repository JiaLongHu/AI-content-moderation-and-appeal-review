from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_appeals import submit_appeal
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_reject_appeal_approve_and_public_visibility_flow(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L2, 1.0))
    user_a = auth_headers(client, "user_a")
    content_id = client.post(
        "/api/v1/posts",
        json={"title": "完整流程", "body": "需要人工复核的演示内容"},
        headers=user_a,
    ).json()["id"]

    reviewer = auth_headers(client, "content_reviewer")
    task_id = client.get("/api/v1/moderation/tasks", headers=reviewer).json()[0]["id"]
    client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json={"final_category": "harassment", "final_level": "L3", "decision": "reject"},
        headers=reviewer,
    )
    assert client.get("/api/v1/posts", headers=auth_headers(client, "user_b")).json() == []

    appeal_id = submit_appeal(client, content_id)["id"]
    appeal_reviewer = auth_headers(client, "appeal_reviewer")
    client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={
            "final_category": "normal",
            "final_level": "L0",
            "decision": "approved",
            "result_reason": "结合申诉说明和原文，确认内容可以发布。",
        },
        headers=appeal_reviewer,
    )

    public_posts = client.get("/api/v1/posts", headers=auth_headers(client, "user_b")).json()
    assert [post["id"] for post in public_posts] == [content_id]
    assert "moderation" not in public_posts[0]
