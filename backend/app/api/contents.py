from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.security import require_roles
from backend.app.db.session import get_db
from backend.app.models import (
    Content,
    ContentStatus,
    ContentType,
    ModerationResult,
    ReviewTask,
    Role,
    User,
)
from backend.app.moderation import AIReviewClient, ModerationAction, ModerationService
from backend.app.schemas.contents import (
    CommentCreate,
    ModerationSummary,
    MyContentItem,
    PostCreate,
    PublicComment,
    PublicPost,
    PublicPostDetail,
    PublicReply,
    SubmissionResponse,
)

router = APIRouter(tags=["forum"])
require_user = require_roles(Role.USER)


def get_moderation_service() -> ModerationService:
    return ModerationService(AIReviewClient())


def moderation_summary(result: ModerationResult) -> ModerationSummary:
    return ModerationSummary(
        categories=result.categories,
        confidences=result.confidences,
        final_category=result.final_category,
        final_level=result.final_level,
        reason=result.reason,
    )


async def moderate_and_save(
    db: Session,
    content: Content,
    service: ModerationService,
    text: str,
    context: str | None = None,
) -> SubmissionResponse:
    decision = await service.review(text, context)
    result = ModerationResult(
        content_id=content.id,
        categories=[category.value for category in decision.categories],
        confidences={category.value: value for category, value in decision.confidences.items()},
        final_category=decision.final_category,
        final_level=decision.final_level,
        reason=decision.reason,
    )
    db.add(result)

    if decision.action is ModerationAction.PUBLISH:
        content.status = ContentStatus.PUBLISHED
        content.published_at = datetime.now(UTC)
    elif decision.action is ModerationAction.REJECT:
        content.status = ContentStatus.REJECTED
    else:
        content.status = ContentStatus.PENDING_MANUAL_REVIEW
        db.add(ReviewTask(content_id=content.id))

    db.commit()
    db.refresh(content)
    db.refresh(result)
    return SubmissionResponse(
        id=content.id,
        content_type=content.content_type,
        status=content.status,
        moderation=moderation_summary(result),
    )


@router.post("/posts", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    payload: PostCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> SubmissionResponse:
    content = Content(
        author_id=user.id,
        content_type=ContentType.POST,
        title=payload.title,
        body=payload.body,
    )
    db.add(content)
    db.flush()
    return await moderate_and_save(
        db,
        content,
        service,
        f"标题：{payload.title}\n正文：{payload.body}",
    )


@router.get("/posts", response_model=list[PublicPost])
def list_posts(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
) -> list[PublicPost]:
    del user
    rows = db.execute(
        select(Content, User.username)
        .join(User, User.id == Content.author_id)
        .where(
            Content.content_type == ContentType.POST,
            Content.status == ContentStatus.PUBLISHED,
        )
        .order_by(Content.published_at.desc(), Content.id.desc())
    ).all()
    return [
        PublicPost(
            id=content.id,
            author=username,
            title=content.title or "",
            body=content.body,
            created_at=content.created_at,
        )
        for content, username in rows
    ]


def get_published_post(db: Session, post_id: int) -> Content:
    post = db.scalar(
        select(Content).where(
            Content.id == post_id,
            Content.content_type == ContentType.POST,
            Content.status == ContentStatus.PUBLISHED,
        )
    )
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在或尚未发布")
    return post


def get_commentable_post(db: Session, post_id: int) -> Content:
    post = db.scalar(
        select(Content).where(
            Content.id == post_id,
            Content.content_type == ContentType.POST,
        )
    )
    if post is None:
        raise HTTPException(status_code=404, detail="帖子不存在")
    if post.status is not ContentStatus.PUBLISHED:
        raise HTTPException(status_code=409, detail="当前帖子暂不可评论")
    return post


@router.get("/posts/{post_id}", response_model=PublicPostDetail)
def post_detail(
    post_id: int,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
) -> PublicPostDetail:
    del user
    post = get_published_post(db, post_id)
    author = db.get(User, post.author_id)
    comments = list(
        db.scalars(
            select(Content)
            .where(
                Content.post_id == post.id,
                Content.content_type == ContentType.COMMENT,
                Content.status == ContentStatus.PUBLISHED,
            )
            .order_by(Content.published_at.asc(), Content.id.asc())
        )
    )
    replies = list(
        db.scalars(
            select(Content)
            .where(
                Content.post_id == post.id,
                Content.content_type == ContentType.REPLY,
                Content.status == ContentStatus.PUBLISHED,
            )
            .order_by(Content.published_at.asc(), Content.id.asc())
        )
    )
    author_ids = {post.author_id, *(item.author_id for item in comments + replies)}
    usernames = dict(
        db.execute(select(User.id, User.username).where(User.id.in_(author_ids))).all()
    )
    replies_by_comment: dict[int, list[PublicReply]] = {}
    for reply in replies:
        if reply.parent_comment_id is not None:
            replies_by_comment.setdefault(reply.parent_comment_id, []).append(
                PublicReply(
                    id=reply.id,
                    author=usernames[reply.author_id],
                    body=reply.body,
                    created_at=reply.created_at,
                )
            )
    return PublicPostDetail(
        id=post.id,
        author=author.username if author else "未知用户",
        title=post.title or "",
        body=post.body,
        created_at=post.created_at,
        comments=[
            PublicComment(
                id=comment.id,
                author=usernames[comment.author_id],
                body=comment.body,
                created_at=comment.created_at,
                replies=replies_by_comment.get(comment.id, []),
            )
            for comment in comments
        ],
    )


@router.post(
    "/posts/{post_id}/comments",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> SubmissionResponse:
    post = get_commentable_post(db, post_id)
    content = Content(
        author_id=user.id,
        content_type=ContentType.COMMENT,
        body=payload.body,
        post_id=post.id,
    )
    db.add(content)
    db.flush()
    context = f"所属帖子标题：{post.title}\n所属帖子正文：{post.body}"
    return await moderate_and_save(db, content, service, payload.body, context)


@router.post(
    "/comments/{comment_id}/replies",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reply(
    comment_id: int,
    payload: CommentCreate,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
    service: Annotated[ModerationService, Depends(get_moderation_service)],
) -> SubmissionResponse:
    comment = db.scalar(
        select(Content).where(
            Content.id == comment_id,
            Content.content_type == ContentType.COMMENT,
            Content.status == ContentStatus.PUBLISHED,
        )
    )
    if comment is None or comment.post_id is None:
        raise HTTPException(status_code=409, detail="当前评论暂不可回复")
    post = get_published_post(db, comment.post_id)
    content = Content(
        author_id=user.id,
        content_type=ContentType.REPLY,
        body=payload.body,
        post_id=post.id,
        parent_comment_id=comment.id,
    )
    db.add(content)
    db.flush()
    context = (
        f"直接父评论：{comment.body}\n所属帖子标题：{post.title}\n所属帖子正文：{post.body}"
    )
    return await moderate_and_save(db, content, service, payload.body, context)


@router.get("/me/contents", response_model=list[MyContentItem])
def my_contents(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(require_user)],
) -> list[MyContentItem]:
    rows = db.execute(
        select(Content, ModerationResult)
        .join(ModerationResult, ModerationResult.content_id == Content.id)
        .where(Content.author_id == user.id)
        .order_by(Content.created_at.desc(), Content.id.desc())
    ).all()
    return [
        MyContentItem(
            id=content.id,
            content_type=content.content_type,
            title=content.title,
            body=content.body,
            post_id=content.post_id,
            parent_comment_id=content.parent_comment_id,
            status=content.status,
            created_at=content.created_at,
            moderation=moderation_summary(result),
        )
        for content, result in rows
    ]
