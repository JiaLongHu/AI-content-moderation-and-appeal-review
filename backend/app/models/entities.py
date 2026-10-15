from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base
from backend.app.models.enums import (
    AppealStatus,
    ContentStatus,
    ContentType,
    Decision,
    ReviewTaskStatus,
    RiskCategory,
    RiskLevel,
    Role,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, native_enum=False), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class Content(Base):
    __tablename__ = "contents"

    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, native_enum=False),
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body: Mapped[str] = mapped_column(Text)
    post_id: Mapped[int | None] = mapped_column(ForeignKey("contents.id"), nullable=True)
    parent_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey("contents.id"),
        nullable=True,
    )
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, native_enum=False),
        default=ContentStatus.AUTO_REVIEWING,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ModerationResult(Base):
    __tablename__ = "moderation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), unique=True, index=True)
    categories: Mapped[list[str]] = mapped_column(JSON)
    confidences: Mapped[dict[str, float]] = mapped_column(JSON)
    final_category: Mapped[RiskCategory] = mapped_column(
        Enum(RiskCategory, native_enum=False)
    )
    final_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel, native_enum=False))
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), unique=True, index=True)
    status: Mapped[ReviewTaskStatus] = mapped_column(
        Enum(ReviewTaskStatus, native_enum=False),
        default=ReviewTaskStatus.PENDING,
        index=True,
    )
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision: Mapped[Decision | None] = mapped_column(
        Enum(Decision, native_enum=False),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Appeal(Base):
    __tablename__ = "appeals"

    id: Mapped[int] = mapped_column(primary_key=True)
    content_id: Mapped[int] = mapped_column(ForeignKey("contents.id"), unique=True, index=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    reason: Mapped[str] = mapped_column(String(500))
    status: Mapped[AppealStatus] = mapped_column(
        Enum(AppealStatus, native_enum=False),
        default=AppealStatus.PENDING,
        index=True,
    )
    reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    final_category: Mapped[RiskCategory | None] = mapped_column(
        Enum(RiskCategory, native_enum=False),
        nullable=True,
    )
    final_level: Mapped[RiskLevel | None] = mapped_column(
        Enum(RiskLevel, native_enum=False),
        nullable=True,
    )
    result_reason: Mapped[str | None] = mapped_column(String(300), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
