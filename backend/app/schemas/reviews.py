from datetime import datetime

from pydantic import BaseModel, model_validator

from backend.app.models import ContentStatus, ContentType, Decision, RiskCategory, RiskLevel
from backend.app.schemas.contents import ModerationSummary


class ReviewTaskItem(BaseModel):
    id: int
    content_id: int
    content_type: ContentType
    author: str
    title: str | None
    body: str
    content_status: ContentStatus
    task_status: str
    decision: Decision | None
    reviewer: str | None
    completed_at: datetime | None
    created_at: datetime
    context: str | None = None
    moderation: ModerationSummary


class ReviewDecisionRequest(BaseModel):
    final_category: RiskCategory
    final_level: RiskLevel
    decision: Decision

    @model_validator(mode="after")
    def validate_decision_matches_level(self) -> "ReviewDecisionRequest":
        if self.final_level is RiskLevel.L2:
            raise ValueError("L2不能作为人工审核终态")
        if (
            self.final_level in {RiskLevel.L0, RiskLevel.L1}
            and self.decision is not Decision.PUBLISH
        ):
            raise ValueError("L0或L1只能通过并发布")
        if (
            self.final_level in {RiskLevel.L3, RiskLevel.L4}
            and self.decision is not Decision.REJECT
        ):
            raise ValueError("L3或L4只能拒绝发布")
        return self
