import re

from backend.app.models import RiskCategory, RiskLevel
from backend.app.moderation.schemas import CategoryScore, ModerationOutput


class TextRuleEngine:
    _illegal_patterns = tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"出售.{0,4}(枪支|毒品)",
            r"(代开|出售).{0,4}发票",
            r"银行卡.{0,4}套现",
            r"制作.{0,4}(炸弹|爆炸物)",
        )
    )
    _promotion_pattern = re.compile(
        r"(加微(?:信)?|联系微(?:信)?|推广合作|低价代购|兼职刷单|返利赚钱|扫码咨询)",
        re.IGNORECASE,
    )
    _contact_pattern = re.compile(
        r"(?:1[3-9]\d{9}|QQ\s*[:：]?\s*[1-9]\d{4,11}|(?:微信|vx)\s*[:：]?\s*[A-Za-z][-_A-Za-z0-9]{5,19})",
        re.IGNORECASE,
    )

    def evaluate(self, text: str) -> ModerationOutput | None:
        if any(pattern.search(text) for pattern in self._illegal_patterns):
            return ModerationOutput(
                categories=[
                    CategoryScore(category=RiskCategory.ILLEGAL_FRAUD, confidence=0.99)
                ],
                final_category=RiskCategory.ILLEGAL_FRAUD,
                final_level=RiskLevel.L4,
                reason="内容包含明确的违禁交易或危险物品信息",
            )

        if self._promotion_pattern.search(text) and self._contact_pattern.search(text):
            return ModerationOutput(
                categories=[
                    CategoryScore(category=RiskCategory.SPAM_ADVERTISING, confidence=0.95)
                ],
                final_category=RiskCategory.SPAM_ADVERTISING,
                final_level=RiskLevel.L3,
                reason="内容包含明确的广告引流及联系方式",
            )

        return None
