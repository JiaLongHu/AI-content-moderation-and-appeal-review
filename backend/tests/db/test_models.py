from sqlalchemy import inspect
from sqlalchemy.orm import Session


def test_core_tables_exist(db_session: Session) -> None:
    table_names = set(inspect(db_session.get_bind()).get_table_names())
    assert table_names == {
        "appeals",
        "contents",
        "moderation_results",
        "review_tasks",
        "users",
    }

