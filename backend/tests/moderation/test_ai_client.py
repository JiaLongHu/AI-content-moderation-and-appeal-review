import asyncio
import json

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.models import RiskLevel
from backend.app.moderation.ai_client import (
    AIConnectionError,
    AIResponseError,
    AIReviewClient,
    AIServiceError,
    AITimeoutError,
)


def make_settings() -> Settings:
    return Settings(
        jwt_secret_key="test-jwt-secret",
        seed_default_password="test-password",
        ai_api_base_url="https://ai.example.test/v1",
        ai_api_key="test-ai-key",
        ai_model="test-model",
    )


def valid_response() -> dict[str, object]:
    content = json.dumps(
        {
            "categories": [{"category": "normal", "confidence": 0.96}],
            "final_category": "normal",
            "final_level": "L0",
            "reason": "内容正常",
        }
    )
    return {"choices": [{"message": {"content": content}}]}


def test_valid_chat_completion_is_parsed() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=valid_response()))
    result = asyncio.run(AIReviewClient(make_settings(), transport).review("普通内容"))
    assert result.final_level is RiskLevel.L0
    assert result.final_confidence == 0.96


def test_service_error_is_normalized() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503, text="unavailable"))
    with pytest.raises(AIServiceError):
        asyncio.run(AIReviewClient(make_settings(), transport).review("普通内容"))


def test_timeout_is_normalized() -> None:
    def raise_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(AITimeoutError):
        asyncio.run(
            AIReviewClient(make_settings(), httpx.MockTransport(raise_timeout)).review("普通内容")
        )


def test_connection_failure_is_normalized() -> None:
    def raise_connection_error(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("offline", request=request)

    with pytest.raises(AIConnectionError):
        asyncio.run(
            AIReviewClient(
                make_settings(),
                httpx.MockTransport(raise_connection_error),
            ).review("普通内容")
        )


def test_missing_configuration_is_normalized() -> None:
    settings = Settings(jwt_secret_key="test-jwt", seed_default_password="test-password")
    with pytest.raises(AIConnectionError):
        asyncio.run(AIReviewClient(settings).review("普通内容"))


@pytest.mark.parametrize(
    "payload",
    [
        {"not_choices": []},
        {"choices": [{"message": {"content": "not json"}}]},
        {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "categories": [{"category": "normal", "confidence": 2}],
                                "final_category": "normal",
                                "final_level": "L0",
                                "reason": "非法置信度",
                            }
                        )
                    }
                }
            ]
        },
    ],
)
def test_invalid_response_is_rejected(payload: dict[str, object]) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    with pytest.raises(AIResponseError):
        asyncio.run(AIReviewClient(make_settings(), transport).review("普通内容"))
