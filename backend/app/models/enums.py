from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    CONTENT_REVIEWER = "content_reviewer"
    APPEAL_REVIEWER = "appeal_reviewer"


class ContentType(StrEnum):
    POST = "post"
    COMMENT = "comment"
    REPLY = "reply"


class ContentStatus(StrEnum):
    AUTO_REVIEWING = "auto_reviewing"
    PENDING_MANUAL_REVIEW = "pending_manual_review"
    PUBLISHED = "published"
    REJECTED = "rejected"


class RiskLevel(StrEnum):
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class RiskCategory(StrEnum):
    NORMAL = "normal"
    SEXUAL = "sexual"
    VIOLENCE = "violence"
    ILLEGAL_FRAUD = "illegal_fraud"
    HATE_DISCRIMINATION = "hate_discrimination"
    HARASSMENT = "harassment"
    PRIVACY = "privacy"
    SPAM_ADVERTISING = "spam_advertising"


class ReviewTaskStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class Decision(StrEnum):
    PUBLISH = "publish"
    REJECT = "reject"


class AppealStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
