"""add training plans and evaluation scheduling

Revision ID: 3f8a1d6c4b20
Revises: 2c9d1e8f4a6b
Create Date: 2026-07-31 13:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "3f8a1d6c4b20"
down_revision: str | None = "2c9d1e8f4a6b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    columns = {
        column["name"]
        for column in sa.inspect(op.get_bind()).get_columns("evaluaciones")
    }
    additions = {
        "proxima_fecha": sa.Date(),
        "correccion_habilitada_hasta": sa.DateTime(),
        "correccion_habilitada_por_id": sa.Integer(),
        "motivo_correccion": sa.Text(),
        "motivo_anulacion": sa.Text(),
        "anulada_en": sa.DateTime(),
        "anulada_por_usuario_id": sa.Integer(),
    }
    for name, column_type in additions.items():
        if name not in columns:
            op.add_column("evaluaciones", sa.Column(name, column_type, nullable=True))
    op.create_table(
        "evaluacion_versiones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("evaluacion_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("datos", sa.Text(), nullable=False),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
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
            ["evaluacion_id"], ["evaluaciones.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_table(
        "planes_capacitacion",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("trabajador_id", sa.Integer(), nullable=False),
        sa.Column("puesto_id", sa.Integer(), nullable=False),
        sa.Column("evaluacion_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=30), nullable=False),
        sa.Column(
            "estado", sa.String(length=20), server_default="pendiente", nullable=False
        ),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("fecha_inicio", sa.Date(), nullable=False),
        sa.Column("fecha_fin", sa.Date(), nullable=True),
        sa.Column("creado_por_usuario_id", sa.Integer(), nullable=True),
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
            ["trabajador_id"], ["trabajadores.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["puesto_id"], ["puestos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["evaluacion_id"], ["evaluaciones.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(
            ["creado_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_table(
        "planes_capacitacion_actividades",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("actividad_id", sa.Integer(), nullable=False),
        sa.Column("fecha_programada", sa.Date(), nullable=False),
        sa.Column("fecha_reprogramacion_1", sa.Date(), nullable=True),
        sa.Column("fecha_reprogramacion_2", sa.Date(), nullable=True),
        sa.Column("fecha_cumplimiento", sa.Date(), nullable=True),
        sa.Column(
            "estado", sa.String(length=20), server_default="pendiente", nullable=False
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("completada_por_usuario_id", sa.Integer(), nullable=True),
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
            ["plan_id"], ["planes_capacitacion.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["actividad_id"], ["actividades.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["completada_por_usuario_id"], ["usuarios.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    permisos = sa.table(
        "permisos",
        sa.column("codigo", sa.String()),
        sa.column("nombre", sa.String()),
        sa.column("descripcion", sa.Text()),
        sa.column("modulo", sa.String()),
        sa.column("accion", sa.String()),
        sa.column("sistema", sa.Boolean()),
        sa.column("activo", sa.Boolean()),
    )
    codes = [
        (
            "evaluaciones.programar",
            "Programar evaluaciones",
            "evaluaciones",
            "programar",
        ),
        ("evaluaciones.corregir", "Corregir evaluaciones", "evaluaciones", "corregir"),
        (
            "capacitacion.consultar",
            "Consultar capacitación",
            "capacitacion",
            "consultar",
        ),
        (
            "capacitacion.gestionar",
            "Gestionar capacitación",
            "capacitacion",
            "gestionar",
        ),
    ]
    connection = op.get_bind()
    for code, name, module, action in codes:
        exists = connection.execute(
            sa.text("SELECT 1 FROM permisos WHERE codigo = :code"), {"code": code}
        ).scalar()
        if exists is None:
            connection.execute(
                permisos.insert(),
                {
                    "codigo": code,
                    "nombre": name,
                    "descripcion": "Permiso predefinido del sistema",
                    "modulo": module,
                    "accion": action,
                    "sistema": True,
                    "activo": True,
                },
            )
    role_permissions = sa.table(
        "rol_permisos",
        sa.column("rol_id", sa.Integer()),
        sa.column("permiso_id", sa.Integer()),
    )
    admin_id = connection.execute(
        sa.text("SELECT id FROM roles WHERE nombre = 'Administrador'")
    ).scalar_one()
    all_new_ids = (
        connection.execute(
            sa.text(
                "SELECT id FROM permisos WHERE codigo IN ("
                "'evaluaciones.programar', 'evaluaciones.corregir', "
                "'capacitacion.consultar', 'capacitacion.gestionar')"
            )
        )
        .scalars()
        .all()
    )
    for permission_id in all_new_ids:
        exists = connection.execute(
            sa.text(
                "SELECT 1 FROM rol_permisos "
                "WHERE rol_id = :role_id AND permiso_id = :permission_id"
            ),
            {"role_id": admin_id, "permission_id": permission_id},
        ).scalar()
        if exists is None:
            connection.execute(
                role_permissions.insert(),
                {"rol_id": admin_id, "permiso_id": permission_id},
            )
    for role_name, codes_for_role in {
        "Evaluador": [
            "evaluaciones.programar",
            "evaluaciones.corregir",
            "capacitacion.consultar",
        ],
        "Supervisor": ["evaluaciones.programar", "capacitacion.consultar"],
        "Consulta": ["capacitacion.consultar"],
    }.items():
        role_id = connection.execute(
            sa.text("SELECT id FROM roles WHERE nombre = :name"), {"name": role_name}
        ).scalar_one_or_none()
        if role_id is not None:
            ids = (
                connection.execute(
                    sa.text(
                        "SELECT id FROM permisos WHERE codigo IN ("
                        + ",".join(f"'{code}'" for code in codes_for_role)
                        + ")"
                    )
                )
                .scalars()
                .all()
            )
            for permission_id in ids:
                exists = connection.execute(
                    sa.text(
                        "SELECT 1 FROM rol_permisos "
                        "WHERE rol_id = :role_id AND permiso_id = :permission_id"
                    ),
                    {"role_id": role_id, "permission_id": permission_id},
                ).scalar()
                if exists is None:
                    connection.execute(
                        role_permissions.insert(),
                        {"rol_id": role_id, "permiso_id": permission_id},
                    )


def downgrade() -> None:
    op.drop_table("planes_capacitacion_actividades")
    op.drop_table("planes_capacitacion")
    op.drop_table("evaluacion_versiones")
    op.drop_column("evaluaciones", "anulada_por_usuario_id")
    op.drop_column("evaluaciones", "anulada_en")
    op.drop_column("evaluaciones", "motivo_anulacion")
    op.drop_column("evaluaciones", "motivo_correccion")
    op.drop_column("evaluaciones", "correccion_habilitada_por_id")
    op.drop_column("evaluaciones", "correccion_habilitada_hasta")
    op.drop_column("evaluaciones", "proxima_fecha")
