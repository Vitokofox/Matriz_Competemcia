"""add configurable matrix import drafts

Revision ID: 9f1b7c4d6e85
Revises: 8e0a6b3c5d74
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "9f1b7c4d6e85"
down_revision: str | None = "8e0a6b3c5d74"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "borradores_importacion_matriz",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("token", sa.String(36), nullable=False, unique=True),
        sa.Column("archivo_nombre", sa.String(255), nullable=False),
        sa.Column("procedure_code", sa.String(100), nullable=False),
        sa.Column("raw_source_hash", sa.String(64), nullable=False),
        sa.Column("normalized_hash", sa.String(64), nullable=False),
        sa.Column("datos_normalizados", sa.Text(), nullable=False),
        sa.Column("configuracion", sa.Text()),
        sa.Column("estado", sa.String(20), nullable=False, server_default="analizado"),
        sa.Column("errores", sa.Text()),
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
            "estado IN ('analizado', 'configurado', 'validado', "
            "'publicado', 'fallido')",
            name="estado_borrador_importacion_valido",
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
    )


def downgrade() -> None:
    op.drop_table("borradores_importacion_matriz")
