import pytest
from pydantic import ValidationError

from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation.schemas import CategoryScore, ModerationOutput


def test_valid_multi_category_result_exposes_final_confidence() -> None:
    result = ModerationOutput(
        categories=[
            CategoryScore(category=RiskCategory.HARASSMENT, confidence=0.91),
            CategoryScore(category=RiskCategory.VIOLENCE, confidence=0.72),
        ],
        final_category=RiskCategory.HARASSMENT,
        final_level=RiskLevel.L3,
        reason="包含针对他人的攻击性表达",
    )
    assert result.final_confidence == 0.91
    assert result.confidence_by_category[RiskCategory.VIOLENCE] == 0.72


@pytest.mark.parametrize(
    "payload",
    [
        {
            "categories": [{"category": "normal", "confidence": 1.01}],
            "final_category": "normal",
            "final_level": "L0",
            "reason": "正常",
        },
        {
            "categories": [{"category": "unknown", "confidence": 0.9}],
            "final_category": "unknown",
            "final_level": "L3",
            "reason": "非法类别",
        },
        {
            "categories": [{"category": "normal", "confidence": 0.9}],
            "final_category": "violence",
            "final_level": "L3",
            "reason": "最终类别缺失",
        },
        {
            "categories": [
                {"category": "normal", "confidence": 0.9},
                {"category": "normal", "confidence": 0.8},
            ],
            "final_category": "normal",
            "final_level": "L0",
            "reason": "重复类别",
        },
        {
            "categories": [{"category": "violence", "confidence": 0.9}],
            "final_category": "violence",
            "final_level": "L0",
            "reason": "L0类别不一致",
        },
    ],
)
def test_invalid_result_is_rejected(payload: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        ModerationOutput.model_validate(payload)
