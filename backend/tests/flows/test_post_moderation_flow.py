from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_post_flows_to_public_pending_or_rejected_state(client: TestClient) -> None:
    use_results(
        client,
        result(RiskLevel.L0, 0.80),
        result(RiskLevel.L1, 0.79),
        result(RiskLevel.L4, 0.90),
    )
    headers = auth_headers(client)
    statuses = []
    for index in range(3):
        response = client.post(
            "/api/v1/posts",
            json={"title": f"帖子{index}", "body": f"内容{index}"},
            headers=headers,
        )
        statuses.append(response.json()["status"])
    assert statuses == ["published", "pending_manual_review", "rejected"]
    public_posts = client.get("/api/v1/posts", headers=headers).json()
    assert [post["title"] for post in public_posts] == ["帖子0"]
