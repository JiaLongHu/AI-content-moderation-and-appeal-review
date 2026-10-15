from pathlib import Path

from sqlalchemy import select

from backend.app.core.config import get_settings
from backend.app.core.security import hash_password
from backend.app.db.base import Base
from backend.app.db.session import SessionLocal, engine
from backend.app.models import Role, User

PRESET_USERS = (
    ("user_a", Role.USER),
    ("user_b", Role.USER),
    ("content_reviewer", Role.CONTENT_REVIEWER),
    ("appeal_reviewer", Role.APPEAL_REVIEWER),
)


def init_db() -> None:
    settings = get_settings()
    Path("backend/data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    password_digest = hash_password(settings.require_seed_password())
    with SessionLocal.begin() as session:
        existing = set(session.scalars(select(User.username)).all())
        for username, role in PRESET_USERS:
            if username not in existing:
                session.add(
                    User(
                        username=username,
                        password_hash=password_digest,
                        role=role,
                    )
                )


if __name__ == "__main__":
    init_db()

