import asyncio

from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation import ModerationAction, ModerationService
from backend.app.moderation.schemas import CategoryScore, ModerationOutput
from backend.app.moderation.testing import StubAIReviewer


def output(level: RiskLevel, confidence: float) -> ModerationOutput:
    category = RiskCategory.NORMAL if level is RiskLevel.L0 else RiskCategory.HARASSMENT
    return ModerationOutput(
        categories=[CategoryScore(category=category, confidence=confidence)],
        final_category=category,
        final_level=level,
        reason="测试",
    )


def test_context_is_only_added_after_uncertain_first_pass() -> None:
    reviewer = StubAIReviewer(output(RiskLevel.L2, 1.0), output(RiskLevel.L0, 0.9))
    decision = asyncio.run(ModerationService(reviewer).review("当前评论", "最小上下文"))
    assert decision.action is ModerationAction.PUBLISH
    assert reviewer.calls == [("当前评论", None), ("当前评论", "最小上下文")]


def test_confident_first_pass_does_not_send_context() -> None:
    reviewer = StubAIReviewer(output(RiskLevel.L0, 0.9))
    asyncio.run(ModerationService(reviewer).review("当前评论", "最小上下文"))
    assert reviewer.calls == [("当前评论", None)]
