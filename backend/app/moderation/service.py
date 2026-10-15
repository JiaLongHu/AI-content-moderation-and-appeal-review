from typing import Protocol

from backend.app.moderation.ai_client import AIReviewError
from backend.app.moderation.routing import (
    ModerationDecision,
    fallback_decision,
    route_result,
)
from backend.app.moderation.rules import TextRuleEngine
from backend.app.moderation.schemas import ModerationOutput


class AIReviewer(Protocol):
    async def review(self, text: str, context: str | None = None) -> ModerationOutput: ...


class ModerationService:
    def __init__(self, ai_reviewer: AIReviewer, rules: TextRuleEngine | None = None) -> None:
        self.ai_reviewer = ai_reviewer
        self.rules = rules or TextRuleEngine()

    async def review(self, text: str, context: str | None = None) -> ModerationDecision:
        rule_result = self.rules.evaluate(text)
        if rule_result is not None:
            return route_result(rule_result)

        try:
            ai_result = await self.ai_reviewer.review(text)
            decision = route_result(ai_result)
            if context is not None and decision.final_level.value == "L2":
                contextual_result = await self.ai_reviewer.review(text, context)
                return route_result(contextual_result)
            return decision
        except (AIReviewError, ValueError, TypeError):
            return fallback_decision()
