from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_low_confidence_content_enters_and_leaves_manual_queue(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L3, 0.89))
    created = client.post(
        "/api/v1/posts",
        json={"title": "边界风险", "body": "需要审核"},
        headers=auth_headers(client),
    ).json()
    assert created["status"] == "pending_manual_review"
    headers = auth_headers(client, "content_reviewer")
    task = client.get("/api/v1/moderation/tasks", headers=headers).json()[0]
    client.post(
        f"/api/v1/moderation/tasks/{task['id']}/decision",
        json={"final_category": "harassment", "final_level": "L3", "decision": "reject"},
        headers=headers,
    )
    assert client.get("/api/v1/moderation/tasks", headers=headers).json() == []
