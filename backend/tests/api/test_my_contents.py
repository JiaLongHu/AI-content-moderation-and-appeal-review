from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def test_my_contents_only_returns_current_authors_records(client: TestClient) -> None:
    use_results(client, result(RiskLevel.L0, 0.95), result(RiskLevel.L0, 0.95))
    client.post(
        "/api/v1/posts",
        json={"title": "用户A", "body": "A的内容"},
        headers=auth_headers(client, "user_a"),
    )
    client.post(
        "/api/v1/posts",
        json={"title": "用户B", "body": "B的内容"},
        headers=auth_headers(client, "user_b"),
    )
    mine_a = client.get("/api/v1/me/contents", headers=auth_headers(client, "user_a")).json()
    mine_b = client.get("/api/v1/me/contents", headers=auth_headers(client, "user_b")).json()
    assert [item["title"] for item in mine_a] == ["用户A"]
    assert [item["title"] for item in mine_b] == ["用户B"]


def test_my_contents_requires_login(client: TestClient) -> None:
    assert client.get("/api/v1/me/contents").status_code == 401
