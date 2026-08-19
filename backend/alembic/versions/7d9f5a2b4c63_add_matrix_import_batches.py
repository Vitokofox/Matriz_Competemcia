"""add matrix import batches and stable source identity

Revision ID: 7d9f5a2b4c63
Revises: 6c8e4f1a3b52
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "7d9f5a2b4c63"
down_revision: str | None = "6c8e4f1a3b52"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "importaciones_matriz",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("maquina_id", sa.Integer(), nullable=False),
        sa.Column("raw_source_hash", sa.String(64), nullable=False),
        sa.Column("normalized_hash", sa.String(64), nullable=False),
        sa.Column("importer_version", sa.String(20), nullable=False),
        sa.Column("fuente", sa.String(255), nullable=False),
        sa.Column("estado", sa.String(20), nullable=False, server_default="validada"),
        sa.Column("creado_por_usuario_id", sa.Integer()),
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
            "estado IN ('validada', 'publicada', 'fallida')",
            name="estado_importacion_matriz_valido",
        ),
        sa.ForeignKeyConstraint(
            ["maquina_id"], ["maquinas.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.UniqueConstraint(
            "maquina_id",
            "normalized_hash",
            "importer_version",
            name="importacion_maquina_contenido_reglas",
        ),
    )

    with op.batch_alter_table("actividades") as batch_op:
        batch_op.add_column(sa.Column("source_key", sa.String(120)))
        batch_op.create_unique_constraint(
            "uq_actividades_source_key", ["source_key"]
        )

    with op.batch_alter_table("actividad_criterios") as batch_op:
        batch_op.add_column(sa.Column("source_key", sa.String(120)))
        batch_op.create_unique_constraint(
            "uq_actividad_criterios_source_key", ["source_key"]
        )

    with op.batch_alter_table("matriz_puesto_versiones") as batch_op:
        batch_op.drop_constraint(
            "uq_matriz_puesto_versiones_source_hash", type_="unique"
        )
        batch_op.add_column(sa.Column("importacion_id", sa.Integer()))
        batch_op.add_column(
            sa.Column(
                "importer_version",
                sa.String(20),
                nullable=False,
                server_default="1",
            )
        )
        batch_op.create_foreign_key(
            "fk_matriz_version_importacion",
            "importaciones_matriz",
            ["importacion_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_unique_constraint(
            "matriz_puesto_fuente_reglas",
            ["puesto_id", "source_hash", "importer_version"],
        )


def downgrade() -> None:
    with op.batch_alter_table("matriz_puesto_versiones") as batch_op:
        batch_op.drop_constraint("matriz_puesto_fuente_reglas", type_="unique")
        batch_op.drop_constraint(
            "fk_matriz_version_importacion", type_="foreignkey"
        )
        batch_op.drop_column("importer_version")
        batch_op.drop_column("importacion_id")
        batch_op.create_unique_constraint(
            "uq_matriz_puesto_versiones_source_hash", ["source_hash"]
        )
    with op.batch_alter_table("actividad_criterios") as batch_op:
        batch_op.drop_constraint(
            "uq_actividad_criterios_source_key", type_="unique"
        )
        batch_op.drop_column("source_key")
    with op.batch_alter_table("actividades") as batch_op:
        batch_op.drop_constraint("uq_actividades_source_key", type_="unique")
        batch_op.drop_column("source_key")
    op.drop_table("importaciones_matriz")
