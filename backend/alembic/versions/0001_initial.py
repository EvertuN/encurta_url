"""initial: create urls and click_events tables

Revision ID: 0001
Revises:
Create Date: 2026-09-11

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import INET, UUID

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "urls",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("short_code", sa.String(12), nullable=False),
        sa.Column("original_url", sa.Text, nullable=False),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_urls_short_code", "urls", ["short_code"], unique=True)

    op.create_table(
        "click_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("url_id", UUID(as_uuid=True), nullable=False),
        sa.Column("ip", INET, nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
        sa.Column("referer", sa.Text, nullable=True),
        sa.Column(
            "clicked_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_click_events_url_id", "click_events", ["url_id"])
    op.create_foreign_key(
        "fk_click_events_url_id",
        "click_events",
        "urls",
        ["url_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("fk_click_events_url_id", "click_events", type_="foreignkey")
    op.drop_index("ix_click_events_url_id", "click_events")
    op.drop_table("click_events")
    op.drop_index("ix_urls_short_code", "urls")
    op.drop_table("urls")
