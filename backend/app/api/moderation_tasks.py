from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import require_roles
from backend.app.db.session import get_db
from backend.app.models import (
    Content,
    ContentStatus,
    Decision,
    ModerationResult,
    ReviewTask,
    ReviewTaskStatus,
    Role,
    User,
)
from backend.app.schemas.contents import ModerationSummary
from backend.app.schemas.reviews import ReviewDecisionRequest, ReviewTaskItem
from backend.app.services.content_context import build_minimum_context

router = APIRouter(prefix="/moderation/tasks", tags=["manual moderation"])
require_content_reviewer = require_roles(Role.CONTENT_REVIEWER)


def task_item(db: Session, task: ReviewTask, include_context: bool) -> ReviewTaskItem:
    content = db.get(Content, task.content_id)
    if content is None:
        raise HTTPException(status_code=404, detail="审核内容不存在")
    author = db.get(User, content.author_id)
    result = db.scalar(
        select(ModerationResult).where(ModerationResult.content_id == content.id)
    )
    if result is None:
        raise HTTPException(status_code=404, detail="审核结果不存在")
    return ReviewTaskItem(
        id=task.id,
        content_id=content.id,
        content_type=content.content_type,
        author=author.username if author else "未知用户",
        title=content.title,
        body=content.body,
        content_status=content.status,
        created_at=task.created_at,
        context=build_minimum_context(db, content) if include_context else None,
        moderation=ModerationSummary(
            categories=result.categories,
            confidences=result.confidences,
            final_category=result.final_category,
            final_level=result.final_level,
            reason=result.reason,
        ),
    )


@router.get("", response_model=list[ReviewTaskItem])
def list_tasks(
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_content_reviewer)],
) -> list[ReviewTaskItem]:
    del reviewer
    tasks = db.scalars(
        select(ReviewTask)
        .where(ReviewTask.status == ReviewTaskStatus.PENDING)
        .order_by(ReviewTask.created_at.asc(), ReviewTask.id.asc())
    )
    return [task_item(db, task, include_context=False) for task in tasks]


@router.get("/{task_id}", response_model=ReviewTaskItem)
def task_detail(
    task_id: int,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_content_reviewer)],
) -> ReviewTaskItem:
    del reviewer
    task = db.get(ReviewTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")
    return task_item(db, task, include_context=True)


@router.post("/{task_id}/decision", response_model=ReviewTaskItem)
def decide_task(
    task_id: int,
    payload: ReviewDecisionRequest,
    db: Annotated[Session, Depends(get_db)],
    reviewer: Annotated[User, Depends(require_content_reviewer)],
) -> ReviewTaskItem:
    task = db.get(ReviewTask, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="审核任务不存在")
    if task.status is not ReviewTaskStatus.PENDING:
        raise HTTPException(status_code=409, detail="该任务已完成，请刷新列表")

    content = db.get(Content, task.content_id)
    result = db.scalar(
        select(ModerationResult).where(ModerationResult.content_id == task.content_id)
    )
    if content is None or result is None:
        raise HTTPException(status_code=404, detail="审核内容不存在")

    if payload.final_category.value not in result.categories:
        result.categories = [*result.categories, payload.final_category.value]
        result.confidences = {**result.confidences, payload.final_category.value: 0.0}
    result.final_category = payload.final_category
    result.final_level = payload.final_level

    if payload.decision is Decision.PUBLISH:
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.now(UTC)
    else:
        content.status = ContentStatus.REJECTED
        content.published_at = None

    task.status = ReviewTaskStatus.COMPLETED
    task.reviewer_id = reviewer.id
    task.decision = payload.decision
    task.completed_at = datetime.now(UTC)
    db.commit()
    return task_item(db, task, include_context=True)
