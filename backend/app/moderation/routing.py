from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field

from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation.schemas import ModerationOutput

PUBLISH_THRESHOLD = 0.80
REJECT_THRESHOLD = 0.90


class ModerationAction(StrEnum):
    PUBLISH = "publish"
    MANUAL_REVIEW = "manual_review"
    REJECT = "reject"


class ModerationDecision(BaseModel):
    categories: list[RiskCategory]
    confidences: dict[RiskCategory, Annotated[float, Field(ge=0.0, le=1.0)]]
    final_category: RiskCategory
    final_level: RiskLevel
    action: ModerationAction
    reason: Annotated[str, Field(min_length=1, max_length=300)]


def route_result(result: ModerationOutput) -> ModerationDecision:
    confidence = result.final_confidence
    action = ModerationAction.MANUAL_REVIEW
    effective_level = RiskLevel.L2

    if result.final_level in {RiskLevel.L0, RiskLevel.L1} and confidence >= PUBLISH_THRESHOLD:
        action = ModerationAction.PUBLISH
        effective_level = result.final_level
    elif result.final_level in {RiskLevel.L3, RiskLevel.L4} and confidence >= REJECT_THRESHOLD:
        action = ModerationAction.REJECT
        effective_level = result.final_level

    return ModerationDecision(
        categories=[item.category for item in result.categories],
        confidences=result.confidence_by_category,
        final_category=result.final_category,
        final_level=effective_level,
        action=action,
        reason=result.reason,
    )


def fallback_decision() -> ModerationDecision:
    return ModerationDecision(
        categories=[RiskCategory.NORMAL],
        confidences={RiskCategory.NORMAL: 0.0},
        final_category=RiskCategory.NORMAL,
        final_level=RiskLevel.L2,
        action=ModerationAction.MANUAL_REVIEW,
        reason="自动审核暂时无法完成，等待人工审核",
    )
