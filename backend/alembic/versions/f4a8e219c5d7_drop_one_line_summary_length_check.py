"""drop one-line summary length check constraints

Revision ID: f4a8e219c5d7
Revises: e1c7a92f4b83
"""

from typing import Sequence, Union

from alembic import op

revision: str = "f4a8e219c5d7"
down_revision: Union[str, None] = "e1c7a92f4b83"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = ("daily_briefings", "sector_briefings", "market_overviews")

# 길이를 강제하는 DB 체크 제약을 20자→30~40자→50자로 계속 손봐야 했던 이유는
# 결국 "잘라서 저장"이라는 발상 자체가 LLM 출력 편차와 안 맞았기 때문이다
# (2026-07-14~15, 같은 원인으로 3번 500/503 재발). 길이는 이제 프롬프트
# 지시(50자 이하)로만 유도하고, 이를 넘겨도 그대로 저장한다 — 카드 레이아웃이
# 가끔 길어지는 것이 새로고침 자체가 깨지는 것보다 낫다.


def upgrade() -> None:
    for table in _TABLES:
        op.drop_constraint(f"ck_{table}_one_line_summary_length", table, type_="check")


def downgrade() -> None:
    for table in _TABLES:
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
