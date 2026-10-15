import pytest
from fastapi.testclient import TestClient

from backend.app.models import RiskLevel
from backend.tests.api.test_posts import auth_headers, result, use_results


def create_rejected_post(client: TestClient) -> int:
    use_results(client, result(RiskLevel.L3, 0.90))
    return client.post(
        "/api/v1/posts",
        json={"title": "被拒绝帖子", "body": "用于测试申诉的内容"},
        headers=auth_headers(client),
    ).json()["id"]


def submit_appeal(client: TestClient, content_id: int) -> dict[str, object]:
    response = client.post(
        f"/api/v1/contents/{content_id}/appeals",
        json={"reason": "该内容是引用讨论，并非鼓励违规行为。"},
        headers=auth_headers(client),
    )
    assert response.status_code == 201
    return response.json()


def test_author_can_appeal_rejected_content_once(client: TestClient) -> None:
    content_id = create_rejected_post(client)
    appeal = submit_appeal(client, content_id)
    assert appeal["appeal_status"] == "pending"
    assert appeal["content_id"] == content_id
    mine = client.get("/api/v1/me/appeals", headers=auth_headers(client)).json()
    assert [item["id"] for item in mine] == [appeal["id"]]

    duplicate = client.post(
        f"/api/v1/contents/{content_id}/appeals",
        json={"reason": "再次提交相同内容的申诉说明。"},
        headers=auth_headers(client),
    )
    assert duplicate.status_code == 409


def test_non_author_and_non_rejected_content_cannot_be_appealed(client: TestClient) -> None:
    rejected_id = create_rejected_post(client)
    assert client.post(
        f"/api/v1/contents/{rejected_id}/appeals",
        json={"reason": "我不是内容作者，不能发起申诉。"},
        headers=auth_headers(client, "user_b"),
    ).status_code == 403

    use_results(client, result(RiskLevel.L0, 0.95))
    published_id = client.post(
        "/api/v1/posts",
        json={"title": "公开内容", "body": "已经发布的正常内容"},
        headers=auth_headers(client),
    ).json()["id"]
    assert client.post(
        f"/api/v1/contents/{published_id}/appeals",
        json={"reason": "公开内容没有申诉资格。"},
        headers=auth_headers(client),
    ).status_code == 409


@pytest.mark.parametrize("reason", ["太短", "x" * 501])
def test_appeal_reason_length_is_validated(client: TestClient, reason: str) -> None:
    content_id = create_rejected_post(client)
    assert client.post(
        f"/api/v1/contents/{content_id}/appeals",
        json={"reason": reason},
        headers=auth_headers(client),
    ).status_code == 422


def test_appeal_reviewer_can_approve_and_publish(client: TestClient) -> None:
    content_id = create_rejected_post(client)
    appeal_id = submit_appeal(client, content_id)["id"]
    headers = auth_headers(client, "appeal_reviewer")
    assert client.get("/api/v1/appeal-review/tasks", headers=headers).status_code == 200
    detail = client.get(f"/api/v1/appeal-review/tasks/{appeal_id}", headers=headers)
    assert detail.json()["original_moderation"]["final_level"] == "L3"

    decided = client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={
            "final_category": "normal",
            "final_level": "L1",
            "decision": "approved",
            "result_reason": "结合语境后确认属于合理讨论。",
        },
        headers=headers,
    )
    assert decided.status_code == 200
    assert decided.json()["appeal_status"] == "approved"
    assert decided.json()["content_status"] == "published"
    assert client.get("/api/v1/appeal-review/tasks", headers=headers).json() == []
    assert content_id in [item["id"] for item in client.get(
        "/api/v1/posts", headers=auth_headers(client)
    ).json()]

    repeated = client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={
            "final_category": "normal",
            "final_level": "L0",
            "decision": "approved",
            "result_reason": "重复处理。",
        },
        headers=headers,
    )
    assert repeated.status_code == 409


def test_appeal_reviewer_can_reject_appeal(client: TestClient) -> None:
    content_id = create_rejected_post(client)
    appeal_id = submit_appeal(client, content_id)["id"]
    response = client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={
            "final_category": "harassment",
            "final_level": "L3",
            "decision": "rejected",
            "result_reason": "复核后仍属于明确违规内容。",
        },
        headers=auth_headers(client, "appeal_reviewer"),
    )
    assert response.status_code == 200
    assert response.json()["content_status"] == "rejected"


@pytest.mark.parametrize(
    "payload",
    [
        {"final_category": "normal", "final_level": "L2", "decision": "approved"},
        {"final_category": "normal", "final_level": "L0", "decision": "rejected"},
        {"final_category": "harassment", "final_level": "L3", "decision": "approved"},
    ],
)
def test_illegal_appeal_decisions_are_rejected(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    content_id = create_rejected_post(client)
    appeal_id = submit_appeal(client, content_id)["id"]
    response = client.post(
        f"/api/v1/appeal-review/tasks/{appeal_id}/decision",
        json={**payload, "result_reason": "测试非法决定组合。"},
        headers=auth_headers(client, "appeal_reviewer"),
    )
    assert response.status_code == 422


def test_only_appeal_reviewer_can_review_appeals(client: TestClient) -> None:
    content_id = create_rejected_post(client)
    submit_appeal(client, content_id)
    assert client.get(
        "/api/v1/appeal-review/tasks", headers=auth_headers(client)
    ).status_code == 403
    assert client.get(
        "/api/v1/appeal-review/tasks", headers=auth_headers(client, "content_reviewer")
    ).status_code == 403
