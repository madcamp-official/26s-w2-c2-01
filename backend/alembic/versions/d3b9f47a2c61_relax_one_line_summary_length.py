"""relax one-line summary length to max 50 chars (+ ... truncation)

Revision ID: d3b9f47a2c61
Revises: c4f82d6a1e93
"""

from typing import Sequence, Union

from alembic import op

revision: str = "d3b9f47a2c61"
down_revision: Union[str, None] = "c4f82d6a1e93"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("daily_briefings", "sector_briefings", "market_overviews")

# 30~40자 강제 방식이 LLM 재시도를 자주 실패시켜 새로고침이 503으로 떨어지는
# 원인이었다(2026-07-14). 앱 레벨 검증을 50자 초과분을 "..."로 자르는 방식으로
# 바꿨는데, DB의 BETWEEN 30 AND 40 체크 제약이 그대로 남아있어 자른 결과가
# 저장될 때 CheckViolation으로 500이 나는 문제가 있었다. 제약을 앱 로직의
# 최대 길이(50자 + "..." = 53자)에 맞춰 완화한다.


def upgrade() -> None:
    for table in _TABLES:
        # 기존 30~40자 제약이 걸린 채로 53자짜리 값을 UPDATE하면 그 UPDATE
        # 자체가 위반이 되므로, 반드시 제약을 먼저 드롭한 뒤 백필해야 한다.
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
            SET one_line_summary = NULL
            WHERE one_line_summary IS NOT NULL
              AND char_length(one_line_summary) NOT BETWEEN 30 AND 40
            """
        )
        op.create_check_constraint(
            f"ck_{table}_one_line_summary_length",
            table,
            "char_length(one_line_summary) BETWEEN 30 AND 40",
        )
