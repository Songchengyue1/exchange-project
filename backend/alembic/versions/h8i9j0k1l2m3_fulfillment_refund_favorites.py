"""fulfillment refund rejection and favorites

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-05-21

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h8i9j0k1l2m3"
down_revision: Union[str, None] = "g7h8i9j0k1l2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("fulfilled_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("orders", sa.Column("refund_reject_reason", sa.Text(), nullable=True))

    op.create_table(
        "product_favorites",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "product_id", name="uq_product_favorites_user_product"),
    )
    op.create_index("ix_product_favorites_product_id", "product_favorites", ["product_id"])
    op.create_index("ix_product_favorites_user_id", "product_favorites", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_product_favorites_user_id", table_name="product_favorites")
    op.drop_index("ix_product_favorites_product_id", table_name="product_favorites")
    op.drop_table("product_favorites")
    op.drop_column("orders", "refund_reject_reason")
    op.drop_column("orders", "fulfilled_at")
