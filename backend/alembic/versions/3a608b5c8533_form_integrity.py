"""Session invalidation and database guards for existing form rules."""
from alembic import op
import sqlalchemy as sa

revision = "3a608b5c8533"
down_revision = "295fe31b7422"
branch_labels = None
depends_on = None

CHECKS = {
    "usuarios": {"ck_usuario_nombre": "length(btrim(nombre)) BETWEEN 1 AND 160", "ck_usuario_correo": "length(correo) BETWEEN 3 AND 254"},
    "proyectos": {"ck_proyecto_progreso": "progreso BETWEEN 0 AND 100"},
    "eventos": {"ck_evento_cupo": "cupo BETWEEN 1 AND 10000", "ck_evento_precio": "precio BETWEEN 0 AND 100000", "ck_evento_modalidad": "modalidad IN ('Presencial', 'En línea', 'Híbrida')", "ck_evento_estatus": "estatus IN ('Activo', 'Pendiente', 'Inactivo')"},
    "horarios": {"ck_horario_intervalo": "fin > inicio"},
    "tareas": {"ck_tarea_estatus": "estatus IN ('Pendiente', 'Completado')", "ck_tarea_nombre": "length(btrim(nombre)) BETWEEN 1 AND 160"},
    "tutorias": {"ck_tutoria_estatus": "estatus IN ('Confirmada', 'Completado', 'Cancelada')"},
    "publicaciones": {"ck_publicacion_fechas": "vence IS NULL OR vence >= fecha", "ck_publicacion_categoria": "categoria IN ('Noticia', 'Convocatoria', 'Aviso')"},
}


def upgrade():
    connection = op.get_bind()
    duplicates = connection.scalar(sa.text("SELECT count(*) FROM (SELECT lower(trim(correo)) FROM usuarios GROUP BY lower(trim(correo)) HAVING count(*) > 1) AS duplicated"))
    if duplicates:
        raise RuntimeError("Hay correos duplicados al normalizar; resolverlos antes de migrar, sin eliminar cuentas automáticamente.")
    preflight = [
        "SELECT count(*) FROM (SELECT lower(btrim(nombre)) FROM tipos_evento GROUP BY lower(btrim(nombre)) HAVING count(*) > 1) AS duplicated",
        "SELECT count(*) FROM (SELECT slot FROM tutorias WHERE estatus = 'Confirmada' GROUP BY slot HAVING count(*) > 1) AS duplicated",
    ]
    preflight.extend(f'SELECT count(*) FROM "{table}" WHERE NOT ({condition})' for table, checks in CHECKS.items() for condition in checks.values())
    if any(connection.scalar(sa.text(query)) for query in preflight):
        raise RuntimeError("Existen datos incompatibles con las reglas de formularios; revisar antes de migrar, sin modificar registros automáticamente.")
    op.add_column("usuarios", sa.Column("auth_version", sa.Integer(), nullable=False, server_default="0"))
    op.create_index("uq_usuarios_correo_normalizado", "usuarios", [sa.text("lower(btrim(correo))")], unique=True)
    op.create_index("uq_tipos_evento_normalizado", "tipos_evento", [sa.text("lower(btrim(nombre))")], unique=True)
    op.create_index("uq_tutoria_confirmada_slot", "tutorias", ["slot"], unique=True, postgresql_where=sa.text("estatus = 'Confirmada'"))
    for table, checks in CHECKS.items():
        for name, condition in checks.items():
            op.create_check_constraint(name, table, condition)


def downgrade():
    for table, checks in CHECKS.items():
        for name in checks:
            op.drop_constraint(name, table, type_="check")
    op.drop_index("uq_tutoria_confirmada_slot", table_name="tutorias")
    op.drop_index("uq_tipos_evento_normalizado", table_name="tipos_evento")
    op.drop_index("uq_usuarios_correo_normalizado", table_name="usuarios")
    op.drop_column("usuarios", "auth_version")
