"""enforce a single published matrix per position

Revision ID: 8e0a6b3c5d74
Revises: 7d9f5a2b4c63
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "8e0a6b3c5d74"
down_revision: str | None = "7d9f5a2b4c63"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_matriz_puesto_publicada",
        "matriz_puesto_versiones",
        ["puesto_id"],
        unique=True,
        sqlite_where=sa.text("estado = 'publicada'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_matriz_puesto_publicada", table_name="matriz_puesto_versiones"
    )
