import pytest
from fastapi import HTTPException

from backend.app.core.security import require_roles
from backend.app.models import Role, User


def make_user(role: Role) -> User:
    return User(username=f"test-{role.value}", password_hash="unused", role=role)


def test_matching_role_is_allowed() -> None:
    checker = require_roles(Role.CONTENT_REVIEWER)
    user = make_user(Role.CONTENT_REVIEWER)
    assert checker(user) is user


@pytest.mark.parametrize("role", [Role.USER, Role.APPEAL_REVIEWER])
def test_non_matching_role_is_rejected(role: Role) -> None:
    checker = require_roles(Role.CONTENT_REVIEWER)
    with pytest.raises(HTTPException) as error:
        checker(make_user(role))
    assert error.value.status_code == 403


def test_appeal_reviewer_permission_is_separate() -> None:
    checker = require_roles(Role.APPEAL_REVIEWER)
    assert checker(make_user(Role.APPEAL_REVIEWER)).role is Role.APPEAL_REVIEWER
    with pytest.raises(HTTPException):
        checker(make_user(Role.CONTENT_REVIEWER))

