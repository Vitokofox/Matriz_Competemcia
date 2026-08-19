"""add competency dimensions and observable criteria

Revision ID: 4a6c2e9d1f30
Revises: 3f8a1d6c4b20
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "4a6c2e9d1f30"
down_revision: str | None = "3f8a1d6c4b20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("competencias") as batch_op:
        batch_op.add_column(
            sa.Column(
                "dimension",
                sa.String(length=30),
                server_default="tecnica",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column("critica", sa.Boolean(), server_default="0", nullable=False)
        )
        batch_op.add_column(
            sa.Column(
                "nivel_sugerido", sa.Integer(), server_default="3", nullable=False
            )
        )
        batch_op.create_check_constraint(
            "dimension_competencia_valida",
            "dimension IN ('tecnica', 'conductual', 'seguridad', "
            "'calidad', 'coordinacion')",
        )
        batch_op.create_check_constraint(
            "nivel_sugerido_1_5", "nivel_sugerido BETWEEN 1 AND 5"
        )

    op.create_table(
        "actividad_criterios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actividad_id", sa.Integer(), nullable=False),
        sa.Column("descripcion", sa.Text(), nullable=False),
        sa.Column("referencia", sa.String(length=100), nullable=True),
        sa.Column("orden", sa.Integer(), server_default="0", nullable=False),
        sa.Column("critico", sa.Boolean(), server_default="0", nullable=False),
        sa.Column("activo", sa.Boolean(), server_default="1", nullable=False),
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
        sa.CheckConstraint(
            "orden >= 0", name="ck_actividad_criterios_orden_no_negativo"
        ),
        sa.ForeignKeyConstraint(
            ["actividad_id"], ["actividades.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "actividad_criterio_competencias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criterio_id", sa.Integer(), nullable=False),
        sa.Column("competencia_id", sa.Integer(), nullable=False),
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
            ["criterio_id"], ["actividad_criterios.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["competencia_id"], ["competencias.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("criterio_id", "competencia_id"),
    )
    op.create_table(
        "evaluacion_criterios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluacion_id", sa.Integer(), nullable=False),
        sa.Column("criterio_id", sa.Integer(), nullable=False),
        sa.Column("resultado", sa.String(length=20), nullable=False),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("evidencia", sa.Text(), nullable=True),
        sa.Column(
            "critico_incumplido", sa.Boolean(), server_default="0", nullable=False
        ),
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
        sa.CheckConstraint(
            "resultado IN ('cumple', 'parcial', 'no_cumple')",
            name="ck_evaluacion_criterios_resultado_valido",
        ),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"], ["evaluaciones.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["criterio_id"], ["actividad_criterios.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("evaluacion_id", "criterio_id", name="evaluacion_criterio"),
    )


def downgrade() -> None:
    op.drop_table("evaluacion_criterios")
    op.drop_table("actividad_criterio_competencias")
    op.drop_table("actividad_criterios")
    with op.batch_alter_table("competencias") as batch_op:
        batch_op.drop_constraint("nivel_sugerido_1_5", type_="check")
        batch_op.drop_constraint("dimension_competencia_valida", type_="check")
        batch_op.drop_column("nivel_sugerido")
        batch_op.drop_column("critica")
        batch_op.drop_column("dimension")
