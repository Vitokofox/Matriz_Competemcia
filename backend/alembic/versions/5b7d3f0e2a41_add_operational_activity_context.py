"""add operational activity context

Revision ID: 5b7d3f0e2a41
Revises: 4a6c2e9d1f30
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5b7d3f0e2a41"
down_revision: str | None = "4a6c2e9d1f30"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("actividades") as batch_op:
        batch_op.add_column(sa.Column("punto_procedimiento", sa.String(100)))
        batch_op.add_column(sa.Column("referencia", sa.String(100)))
        batch_op.add_column(
            sa.Column("orden", sa.Integer(), server_default="0", nullable=False)
        )

    for table, target, column in (
        ("actividad_areas", "areas.id", "area_id"),
        ("actividad_maquinas", "maquinas.id", "maquina_id"),
    ):
        op.create_table(
            table,
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("actividad_id", sa.Integer(), nullable=False),
            sa.Column(column, sa.Integer(), nullable=False),
            sa.Column(
                "creado_en",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.Column(
                "actualizado_en",
                sa.DateTime(),
                server_default=sa.text("(CURRENT_TIMESTAMP)"),
                nullable=False,
            ),
            sa.ForeignKeyConstraint(
                ["actividad_id"], ["actividades.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint([column], [target], ondelete="RESTRICT"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("actividad_id", column),
        )


def downgrade() -> None:
    op.drop_table("actividad_maquinas")
    op.drop_table("actividad_areas")
    with op.batch_alter_table("actividades") as batch_op:
        batch_op.drop_column("orden")
        batch_op.drop_column("referencia")
        batch_op.drop_column("punto_procedimiento")
