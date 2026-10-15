from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import require_roles
from backend.app.db.session import get_db
from backend.app.models import (
    Appeal,
    AppealStatus,
    Content,
    ContentStatus,
    ModerationResult,
    Role,
    User,
)
from backend.app.schemas.appeals import AppealCreate, AppealDecisionRequest, AppealItem
from backend.app.schemas.contents import ModerationSummary
from backend.app.services.content_context import build_minimum_context

router = APIRouter(tags=["appeals"])
require_user = require_roles(Role.USER)
require_appeal_reviewer = require_roles(Role.APPEAL_REVIEWER)


def appeal_item(db: Session, appeal: Appeal, include_context: bool) -> AppealItem:
    content = db.get(Content, appeal.content_id)
    result = db.scalar(
        select(ModerationResult).where(ModerationResult.content_id == appeal.content_id)
    )
    author = db.get(User, appeal.author_id)
    if content is None or result is None:
        raise HTTPException(status_code=404, detail="申诉关联内容不存在")
    return AppealItem(
        id=appeal.id,
        content_id=content.id,
        author=author.username if author else "未知用户",
        content_type=content.content_type,
        title=content.title,
        body=content.body,
        content_status=content.status,
        appeal_reason=appeal.reason,
        appeal_status=appeal.status,
        created_at=appeal.created_at,
        context=build_minimum_context(db, content) if include_context else None,
        original_moderation=ModerationSummary(
            categories=result.categories,
            confidences=result.confidences,
            final_category=result.final_category,
            final_level=result.final_level,
            reason=result.reason,
        ),
        final_category=appeal.final_category,
        final_level=appeal.final_level,
        result_reason=appeal.result_reason,
    )


@router.post(
    "/contents/{content_id}/appeals",
    response_model=AppealItem,
    status_code=status.HTTP_201_CREATED,
)
def create_appeal(
    content_id: int,
    payload: AppealCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
) -> AppealItem:
    content = db.get(Content, content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="内容不存在")
    if content.author_id != user.id:
        raise HTTPException(status_code=403, detail="只能申诉自己的内容")
    if content.status is not ContentStatus.REJECTED:
        raise HTTPException(status_code=409, detail="只有已拒绝内容可以申诉")
    if db.scalar(select(Appeal).where(Appeal.content_id == content.id)) is not None:
        raise HTTPException(status_code=409, detail="每条内容只能申诉一次")

    appeal = Appeal(content_id=content.id, author_id=user.id, reason=payload.reason)
    db.add(appeal)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="每条内容只能申诉一次") from None
    db.refresh(appeal)
    return appeal_item(db, appeal, include_context=False)


@router.get("/me/appeals", response_model=list[AppealItem])
def my_appeals(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
) -> list[AppealItem]:
    appeals = db.scalars(
        select(Appeal)
        .where(Appeal.author_id == user.id)
        .order_by(Appeal.created_at.desc(), Appeal.id.desc())
    )
    return [appeal_item(db, appeal, include_context=False) for appeal in appeals]


@router.get("/appeal-review/tasks", response_model=list[AppealItem])
def list_appeal_tasks(
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_appeal_reviewer)],
) -> list[AppealItem]:
    del reviewer
    appeals = db.scalars(
        select(Appeal)
        .where(Appeal.status == AppealStatus.PENDING)
        .order_by(Appeal.created_at.asc(), Appeal.id.asc())
    )
    return [appeal_item(db, appeal, include_context=False) for appeal in appeals]


@router.get("/appeal-review/tasks/{appeal_id}", response_model=AppealItem)
def appeal_detail(
    appeal_id: int,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_appeal_reviewer)],
) -> AppealItem:
    del reviewer
    appeal = db.get(Appeal, appeal_id)
    if appeal is None:
        raise HTTPException(status_code=404, detail="申诉不存在")
    return appeal_item(db, appeal, include_context=True)


@router.post("/appeal-review/tasks/{appeal_id}/decision", response_model=AppealItem)
def decide_appeal(
    appeal_id: int,
    payload: AppealDecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_appeal_reviewer)],
) -> AppealItem:
    appeal = db.get(Appeal, appeal_id)
    if appeal is None:
        raise HTTPException(status_code=404, detail="申诉不存在")
    if appeal.status is not AppealStatus.PENDING:
        raise HTTPException(status_code=409, detail="该申诉已完成复核")
    content = db.get(Content, appeal.content_id)
    result = db.scalar(
        select(ModerationResult).where(ModerationResult.content_id == appeal.content_id)
    )
    if content is None or result is None:
        raise HTTPException(status_code=404, detail="申诉关联内容不存在")

    if payload.final_category.value not in result.categories:
        result.categories = [*result.categories, payload.final_category.value]
        result.confidences = {**result.confidences, payload.final_category.value: 0.0}
    result.final_category = payload.final_category
    result.final_level = payload.final_level
    appeal.status = payload.decision
    appeal.reviewer_id = reviewer.id
    appeal.final_category = payload.final_category
    appeal.final_level = payload.final_level
    appeal.result_reason = payload.result_reason
    appeal.completed_at = datetime.now(UTC)

    if payload.decision is AppealStatus.APPROVED:
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.now(UTC)
    else:
        content.status = ContentStatus.REJECTED
        content.published_at = None
    db.commit()
    return appeal_item(db, appeal, include_context=True)
