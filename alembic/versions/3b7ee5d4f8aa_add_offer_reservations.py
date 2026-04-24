"""add offer reservations

Revision ID: 3b7ee5d4f8aa
Revises: 8ae4f4d7264c
Create Date: 2026-04-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3b7ee5d4f8aa"
down_revision: str | None = "8ae4f4d7264c"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
  reservation_status = sa.Enum(
    "pending",
    "confirmed",
    "cancelled",
    "expired",
    name="offer_reservation_status",
  )
  reservation_status.create(op.get_bind(), checkfirst=True)

  op.create_table(
    "offer_reservations",
    sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
    sa.Column("reservation_id", sa.String(length=64), nullable=False),
    sa.Column("offer_id", sa.BigInteger(), nullable=False),
    sa.Column("quantity", sa.Integer(), nullable=False),
    sa.Column("reservation_owner", sa.BigInteger(), nullable=False),
    sa.Column("status", reservation_status, server_default="pending", nullable=False),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
      "created_at",
      sa.DateTime(timezone=True),
      server_default=sa.text("CURRENT_TIMESTAMP"),
      nullable=False,
    ),
    sa.ForeignKeyConstraint(["offer_id"], ["offers.id"], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint("id", name=op.f("pk_offer_reservations")),
    sa.UniqueConstraint("reservation_id", name=op.f("uq_offer_reservations_reservation_id")),
  )
  op.create_index(op.f("ix_offer_reservations_offer_id"), "offer_reservations", ["offer_id"], unique=False)
  op.create_index(op.f("ix_offer_reservations_expires_at"), "offer_reservations", ["expires_at"], unique=False)


def downgrade() -> None:
  op.drop_index(op.f("ix_offer_reservations_expires_at"), table_name="offer_reservations")
  op.drop_index(op.f("ix_offer_reservations_offer_id"), table_name="offer_reservations")
  op.drop_table("offer_reservations")
  sa.Enum(name="offer_reservation_status").drop(op.get_bind(), checkfirst=True)
