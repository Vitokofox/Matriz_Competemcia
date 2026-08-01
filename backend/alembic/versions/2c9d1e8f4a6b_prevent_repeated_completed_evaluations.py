"""prevent repeated completed evaluations

Revision ID: 2c9d1e8f4a6b
Revises: f8710cf39a68
Create Date: 2026-07-31 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "2c9d1e8f4a6b"
down_revision: str | None = "f8710cf39a68"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Preserve the most recent result where legacy data contains duplicates.
    op.execute(
        sa.text(
            """
            UPDATE evaluaciones
            SET estado = 'anulada'
            WHERE estado = 'completada'
              AND id NOT IN (
                  SELECT MAX(id)
                  FROM evaluaciones
                  WHERE estado = 'completada'
                  GROUP BY trabajador_id, puesto_id
              )
            """
        )
    )
    op.create_index(
        "uq_evaluacion_trabajador_puesto_completada",
        "evaluaciones",
        ["trabajador_id", "puesto_id"],
        unique=True,
        sqlite_where=sa.text("estado = 'completada'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_evaluacion_trabajador_puesto_completada", table_name="evaluaciones"
    )
