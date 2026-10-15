from fastapi.testclient import TestClient

from backend.tests.conftest import TEST_PASSWORD


def test_all_preset_users_can_login(client: TestClient) -> None:
    for username, role in (
        ("user_a", "user"),
        ("user_b", "user"),
        ("content_reviewer", "content_reviewer"),
        ("appeal_reviewer", "appeal_reviewer"),
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": TEST_PASSWORD},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["token_type"] == "bearer"
        assert payload["access_token"]
        assert payload["user"]["role"] == role


def test_invalid_password_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "user_a", "password": "incorrect"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "用户名或密码错误"


def test_current_user_requires_valid_token(client: TestClient) -> None:
    unauthorized = client.get("/api/v1/auth/me")
    assert unauthorized.status_code == 401

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "user_a", "password": TEST_PASSWORD},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["username"] == "user_a"

