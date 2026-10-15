from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_appeals import submit_appeal
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_manually_rejected_content_can_complete_appeal_flow(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L2, 1.0))
    content_id = client.post(
        "/api/v1/posts",
        json={"title": "人工审核内容", "body": "先拒绝后申诉"},
        headers=auth_headers(client),
    ).json()["id"]
    reviewer_headers = auth_headers(client, "content_reviewer")
    task_id = client.get("/api/v1/moderation/tasks", headers=reviewer_headers).json()[0]["id"]
    client.post(
        f"/api/v1/moderation/tasks/{task_id}/decision",
        json={"final_category": "harassment", "final_level": "L3", "decision": "reject"},
        headers=reviewer_headers,
    )

    appeal_id = submit_appeal(client, content_id)["id"]
    appeal_headers = auth_headers(client, "appeal_reviewer")
    final = client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={
            "final_category": "normal",
            "final_level": "L0",
            "decision": "approved",
            "result_reason": "人工复核后确认可以发布。",
        },
        headers=appeal_headers,
    )
    assert final.json()["content_status"] == "published"
