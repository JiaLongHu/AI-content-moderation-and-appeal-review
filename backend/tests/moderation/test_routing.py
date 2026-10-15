import asyncio

import pytest

from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation.ai_client import AITimeoutError
from backend.app.moderation.routing import ModerationAction, route_result
from backend.app.moderation.schemas import CategoryScore, ModerationOutput
from backend.app.moderation.service import ModerationService
from backend.app.moderation.testing import StubAIReviewer


def make_result(level: RiskLevel, confidence: float) -> ModerationOutput:
    category = RiskCategory.NORMAL if level is RiskLevel.L0 else RiskCategory.HARASSMENT
    return ModerationOutput(
        categories=[CategoryScore(category=category, confidence=confidence)],
        final_category=category,
        final_level=level,
        reason="测试审核结果",
    )


@pytest.mark.parametrize(
    ("level", "confidence", "action", "effective_level"),
    [
        (RiskLevel.L0, 0.79, ModerationAction.MANUAL_REVIEW, RiskLevel.L2),
        (RiskLevel.L0, 0.80, ModerationAction.PUBLISH, RiskLevel.L0),
        (RiskLevel.L1, 0.79, ModerationAction.MANUAL_REVIEW, RiskLevel.L2),
        (RiskLevel.L1, 0.80, ModerationAction.PUBLISH, RiskLevel.L1),
        (RiskLevel.L2, 1.00, ModerationAction.MANUAL_REVIEW, RiskLevel.L2),
        (RiskLevel.L3, 0.89, ModerationAction.MANUAL_REVIEW, RiskLevel.L2),
        (RiskLevel.L3, 0.90, ModerationAction.REJECT, RiskLevel.L3),
        (RiskLevel.L4, 0.89, ModerationAction.MANUAL_REVIEW, RiskLevel.L2),
        (RiskLevel.L4, 0.90, ModerationAction.REJECT, RiskLevel.L4),
    ],
)
def test_threshold_boundaries(
    level: RiskLevel,
    confidence: float,
    action: ModerationAction,
    effective_level: RiskLevel,
) -> None:
    decision = route_result(make_result(level, confidence))
    assert decision.action is action
    assert decision.final_level is effective_level


def test_multi_category_uses_final_category_confidence() -> None:
    result = ModerationOutput(
        categories=[
            CategoryScore(category=RiskCategory.VIOLENCE, confidence=0.99),
            CategoryScore(category=RiskCategory.HARASSMENT, confidence=0.89),
        ],
        final_category=RiskCategory.HARASSMENT,
        final_level=RiskLevel.L3,
        reason="存在多类风险",
    )
    assert route_result(result).action is ModerationAction.MANUAL_REVIEW


def test_ai_failure_safely_degrades_to_l2() -> None:
    service = ModerationService(StubAIReviewer(AITimeoutError("timeout")))
    decision = asyncio.run(service.review("一段没有命中规则的文字"))
    assert decision.action is ModerationAction.MANUAL_REVIEW
    assert decision.final_level is RiskLevel.L2
    assert decision.reason == "自动审核暂时无法完成，等待人工审核"


def test_rule_match_skips_ai_call() -> None:
    reviewer = StubAIReviewer(make_result(RiskLevel.L0, 0.99))
    service = ModerationService(reviewer)
    decision = asyncio.run(service.review("出售毒品，可当面交易"))
    assert decision.action is ModerationAction.REJECT
    assert reviewer.calls == []
