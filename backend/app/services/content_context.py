from sqlalchemy.orm import Session

from backend.app.models import Content, ContentType


def build_minimum_context(db: Session, content: Content) -> str | None:
    if content.content_type is ContentType.POST:
        return None

    post = db.get(Content, content.post_id) if content.post_id is not None else None
    if post is None:
        return None

    post_context = f"所属帖子标题：{post.title}\n所属帖子正文：{post.body}"
    if content.content_type is ContentType.COMMENT:
        return post_context

    parent = (
        db.get(Content, content.parent_comment_id)
        if content.parent_comment_id is not None
        else None
    )
    if parent is None:
        return post_context
    return f"直接父评论：{parent.body}\n{post_context}"
