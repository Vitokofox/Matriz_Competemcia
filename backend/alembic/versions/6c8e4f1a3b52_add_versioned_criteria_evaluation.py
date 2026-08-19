"""add versioned criteria evaluation

Revision ID: 6c8e4f1a3b52
Revises: 5b7d3f0e2a41
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6c8e4f1a3b52"
down_revision: str | None = "5b7d3f0e2a41"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
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
    )


def upgrade() -> None:
    # La escala anterior no tenía semántica definida. Se eliminan sus resultados
    # y los planes derivados, conservando los planes creados manualmente.
    op.execute("DELETE FROM planes_capacitacion WHERE evaluacion_id IS NOT NULL")
    op.execute("DELETE FROM evaluacion_versiones")
    op.execute("DELETE FROM evaluacion_detalles")
    op.execute("DELETE FROM evaluaciones")
    op.drop_index(
        "uq_evaluacion_trabajador_puesto_completada", table_name="evaluaciones"
    )
    op.drop_table("evaluacion_criterios")

    with op.batch_alter_table("competencias") as batch_op:
        batch_op.drop_constraint("nivel_sugerido_1_5", type_="check")
        batch_op.create_check_constraint(
            "nivel_sugerido_0_4", "nivel_sugerido BETWEEN 0 AND 4"
        )

    with op.batch_alter_table("puesto_actividad_competencias") as batch_op:
        batch_op.drop_constraint("nivel_minimo_1_5", type_="check")
        batch_op.create_check_constraint(
            "nivel_minimo_0_4", "nivel_minimo BETWEEN 0 AND 4"
        )

    op.create_table(
        "matriz_puesto_versiones",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("puesto_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="borrador"),
        sa.Column("source_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("fuente", sa.String(255)),
        sa.Column("publicada_en", sa.DateTime()),
        *timestamps(),
        sa.CheckConstraint(
            "estado IN ('borrador', 'publicada', 'retirada')",
            name="estado_matriz_valido",
        ),
        sa.ForeignKeyConstraint(["puesto_id"], ["puestos.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("puesto_id", "version", name="matriz_puesto_version"),
    )

    with op.batch_alter_table("puesto_actividades") as batch_op:
        batch_op.drop_constraint("puesto_actividad", type_="unique")
        batch_op.add_column(sa.Column("matriz_version_id", sa.Integer()))
        batch_op.create_foreign_key(
            "fk_puesto_actividad_matriz_version",
            "matriz_puesto_versiones",
            ["matriz_version_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_unique_constraint(
            "puesto_actividad_version",
            ["puesto_id", "actividad_id", "matriz_version_id"],
        )

    op.create_table(
        "puesto_actividad_criterios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("puesto_actividad_id", sa.Integer(), nullable=False),
        sa.Column("criterio_id", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(120), nullable=False),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("obligatorio", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("critico", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["puesto_actividad_id"], ["puesto_actividades.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["criterio_id"], ["actividad_criterios.id"], ondelete="RESTRICT"
        ),
        sa.UniqueConstraint("puesto_actividad_id", "source_key"),
        sa.UniqueConstraint("puesto_actividad_id", "criterio_id"),
    )
    op.create_table(
        "puesto_actividad_criterio_requisitos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("puesto_criterio_id", sa.Integer(), nullable=False),
        sa.Column("requisito_id", sa.Integer(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["puesto_criterio_id"],
            ["puesto_actividad_criterios.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requisito_id"],
            ["puesto_actividad_competencias.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("puesto_criterio_id", "requisito_id"),
    )
    op.create_table(
        "criterio_indicadores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("puesto_criterio_id", sa.Integer(), nullable=False),
        sa.Column("categoria", sa.String(30), nullable=False),
        sa.Column("texto", sa.Text(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(
            ["puesto_criterio_id"],
            ["puesto_actividad_criterios.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint("puesto_criterio_id", "categoria", "texto"),
    )

    with op.batch_alter_table("evaluacion_detalles") as batch_op:
        batch_op.drop_constraint("nivel_obtenido_1_5", type_="check")
        batch_op.drop_constraint("nivel_minimo_1_5", type_="check")
        batch_op.create_check_constraint(
            "nivel_obtenido_0_4", "nivel_obtenido BETWEEN 0 AND 4"
        )
        batch_op.create_check_constraint(
            "nivel_minimo_0_4", "nivel_minimo BETWEEN 0 AND 4"
        )

    with op.batch_alter_table("evaluaciones") as batch_op:
        batch_op.add_column(sa.Column("matriz_version_id", sa.Integer()))
        batch_op.add_column(sa.Column("resultado", sa.String(20)))
        batch_op.add_column(
            sa.Column("vigente", sa.Boolean(), nullable=False, server_default="0")
        )
        batch_op.create_foreign_key(
            "fk_evaluacion_matriz_version",
            "matriz_puesto_versiones",
            ["matriz_version_id"],
            ["id"],
            ondelete="RESTRICT",
        )

    op.create_table(
        "evaluacion_criterios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("evaluacion_id", sa.Integer(), nullable=False),
        sa.Column("puesto_criterio_id", sa.Integer(), nullable=False),
        sa.Column("nivel_obtenido", sa.Integer(), nullable=False),
        sa.Column("observaciones", sa.Text()),
        sa.Column("evidencia", sa.Text()),
        sa.Column("actividad_nombre", sa.String(150), nullable=False),
        sa.Column("criterio_descripcion", sa.Text(), nullable=False),
        sa.Column("referencia", sa.String(100)),
        sa.Column("orden", sa.Integer(), nullable=False),
        sa.Column("critico", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column(
            "critico_incumplido", sa.Boolean(), nullable=False, server_default="0"
        ),
        *timestamps(),
        sa.CheckConstraint("nivel_obtenido BETWEEN 0 AND 4", name="nivel_criterio_0_4"),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"], ["evaluaciones.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["puesto_criterio_id"],
            ["puesto_actividad_criterios.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "evaluacion_id", "puesto_criterio_id", name="evaluacion_puesto_criterio"
        ),
    )


def downgrade() -> None:
    op.drop_table("evaluacion_criterios")
    with op.batch_alter_table("evaluaciones") as batch_op:
        batch_op.drop_constraint("fk_evaluacion_matriz_version", type_="foreignkey")
        batch_op.drop_column("vigente")
        batch_op.drop_column("resultado")
        batch_op.drop_column("matriz_version_id")
    op.drop_table("criterio_indicadores")
    op.drop_table("puesto_actividad_criterio_requisitos")
    op.drop_table("puesto_actividad_criterios")
    with op.batch_alter_table("puesto_actividades") as batch_op:
        batch_op.drop_constraint("puesto_actividad_version", type_="unique")
        batch_op.drop_constraint(
            "fk_puesto_actividad_matriz_version", type_="foreignkey"
        )
        batch_op.drop_column("matriz_version_id")
        batch_op.create_unique_constraint(
            "puesto_actividad", ["puesto_id", "actividad_id"]
        )
    op.drop_table("matriz_puesto_versiones")
