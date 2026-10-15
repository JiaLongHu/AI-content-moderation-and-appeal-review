from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation.rules import TextRuleEngine


def test_explicit_illegal_trade_is_matched() -> None:
    result = TextRuleEngine().evaluate("低价出售枪支，支持同城交易")
    assert result is not None
    assert result.final_category is RiskCategory.ILLEGAL_FRAUD
    assert result.final_level is RiskLevel.L4


def test_advertising_with_contact_is_matched() -> None:
    result = TextRuleEngine().evaluate("兼职刷单返利赚钱，加微信 vx: abc_123")
    assert result is not None
    assert result.final_category is RiskCategory.SPAM_ADVERTISING
    assert result.final_level is RiskLevel.L3


def test_contact_without_promotion_is_not_hard_rejected() -> None:
    assert TextRuleEngine().evaluate("快递到了请打电话 13800138000") is None


def test_normal_text_continues_to_ai_layer() -> None:
    assert TextRuleEngine().evaluate("周末有人一起去公园跑步吗？") is None
