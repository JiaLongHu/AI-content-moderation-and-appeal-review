from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator

from backend.app.models import (
    AppealStatus,
    ContentStatus,
    ContentType,
    RiskCategory,
    RiskLevel,
)
from backend.app.schemas.contents import ModerationSummary


class AppealCreate(BaseModel):
    reason: Annotated[str, Field(min_length=10, max_length=500)]

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 10:
            raise ValueError("申诉说明至少需要10个字符")
        return value


class AppealDecisionRequest(BaseModel):
    final_category: RiskCategory
    final_level: RiskLevel
    decision: AppealStatus
    result_reason: Annotated[str, Field(min_length=1, max_length=300)]

    @field_validator("result_reason")
    @classmethod
    def strip_result_reason(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("结果说明不能为空")
        return value

    @model_validator(mode="after")
    def validate_decision_matches_level(self) -> "AppealDecisionRequest":
        if self.decision is AppealStatus.PENDING:
            raise ValueError("待处理不能作为申诉终态")
        if self.final_level is RiskLevel.L2:
            raise ValueError("L2不能作为申诉终审等级")
        if (
            self.final_level in {RiskLevel.L0, RiskLevel.L1}
            and self.decision is not AppealStatus.APPROVED
        ):
            raise ValueError("L0或L1只能通过申诉")
        if (
            self.final_level in {RiskLevel.L3, RiskLevel.L4}
            and self.decision is not AppealStatus.REJECTED
        ):
            raise ValueError("L3或L4只能驳回申诉")
        return self


class AppealItem(BaseModel):
    id: int
    content_id: int
    author: str
    content_type: ContentType
    title: str | None
    body: str
    content_status: ContentStatus
    appeal_reason: str
    appeal_status: AppealStatus
    created_at: datetime
    context: str | None = None
    original_moderation: ModerationSummary
    final_category: RiskCategory | None
    final_level: RiskLevel | None
    result_reason: str | None
