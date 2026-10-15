from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models import ContentStatus, ContentType, RiskCategory, RiskLevel


class PostCreate(BaseModel):
    title: Annotated[str, Field(min_length=1, max_length=100)]
    body: Annotated[str, Field(min_length=1, max_length=3000)]

    @field_validator("title", "body")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class CommentCreate(BaseModel):
    body: Annotated[str, Field(min_length=1, max_length=500)]

    @field_validator("body")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("内容不能为空")
        return value


class ModerationSummary(BaseModel):
    categories: list[RiskCategory]
    confidences: dict[RiskCategory, float]
    final_category: RiskCategory
    final_level: RiskLevel
    reason: str


class SubmissionResponse(BaseModel):
    id: int
    content_type: ContentType
    status: ContentStatus
    moderation: ModerationSummary


class PublicReply(BaseModel):
    id: int
    author: str
    body: str
    created_at: datetime


class PublicComment(PublicReply):
    replies: list[PublicReply]


class PublicPost(BaseModel):
    id: int
    author: str
    title: str
    body: str
    created_at: datetime


class PublicPostDetail(PublicPost):
    comments: list[PublicComment]


class MyContentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: ContentType
    title: str | None
    body: str
    post_id: int | None
    parent_comment_id: int | None
    status: ContentStatus
    created_at: datetime
    moderation: ModerationSummary
