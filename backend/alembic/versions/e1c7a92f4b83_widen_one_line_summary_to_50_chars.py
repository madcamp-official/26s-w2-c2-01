"""widen one-line summary length to max 50 chars (+ ... truncation)

Revision ID: e1c7a92f4b83
Revises: d3b9f47a2c61
"""

from typing import Sequence, Union

from alembic import op

revision: str = "e1c7a92f4b83"
down_revision: Union[str, None] = "d3b9f47a2c61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("daily_briefings", "sector_briefings", "market_overviews")


def upgrade() -> None:
    for table in _TABLES:
        # 기존 <=23 제약이 걸린 채로 그보다 긴 값을 UPDATE하면 그 UPDATE 자체가
        # 위반이 되므로, 반드시 제약을 먼저 드롭한 뒤 백필해야 한다.
        op.drop_constraint(f"ck_{table}_one_line_summary_length", table, type_="check")
        op.execute(
            f"""
            UPDATE {table}
            SET one_line_summary = LEFT(one_line_summary, 50) || '...'
            WHERE one_line_summary IS NOT NULL AND char_length(one_line_summary) > 53
            """
        )
        op.create_check_constraint(
            f"ck_{table}_one_line_summary_length",
            table,
            "char_length(one_line_summary) <= 53",
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_constraint(f"ck_{table}_one_line_summary_length", table, type_="check")
        op.execute(
            f"""
            UPDATE {table}
            SET one_line_summary = LEFT(one_line_summary, 20) || '...'
            WHERE one_line_summary IS NOT NULL AND char_length(one_line_summary) > 23
            """
        )
        op.create_check_constraint(
            f"ck_{table}_one_line_summary_length",
            table,
            "char_length(one_line_summary) <= 23",
        )
