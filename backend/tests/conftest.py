import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["JWT_SECRET_KEY"] = "test-only-jwt-secret-with-sufficient-length"
os.environ["SEED_DEFAULT_PASSWORD"] = "TestOnlyPass123!"

from backend.app.core.config import get_settings  # noqa: E402
from backend.app.core.security import hash_password  # noqa: E402
from backend.app.db.base import Base  # noqa: E402
from backend.app.db.session import get_db  # noqa: E402
from backend.app.main import create_app  # noqa: E402
from backend.app.models import Role, User  # noqa: E402

TEST_PASSWORD = "TestOnlyPass123!"


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    testing_session = sessionmaker(bind=engine, expire_on_commit=False)

    with testing_session() as session:
        for username, role in (
            ("user_a", Role.USER),
            ("user_b", Role.USER),
            ("content_reviewer", Role.CONTENT_REVIEWER),
            ("appeal_reviewer", Role.APPEAL_REVIEWER),
        ):
            session.add(
                User(
                    username=username,
                    password_hash=hash_password(TEST_PASSWORD),
                    role=role,
                )
            )
        session.commit()
        yield session


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    get_settings.cache_clear()
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

