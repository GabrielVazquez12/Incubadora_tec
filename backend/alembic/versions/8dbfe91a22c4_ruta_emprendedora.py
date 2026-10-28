"""Versioned entrepreneurial route, economic history, and assigned actions."""
from alembic import op
import sqlalchemy as sa


revision = '8dbfe91a22c4'
down_revision = '637ddccf1603'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('atenciones_incubadora', sa.Column('evidencia_esperada', sa.String(1000), server_default='', nullable=False))
    op.add_column('configuracion_incubadora', sa.Column('margen_minimo', sa.Numeric(5, 2), server_default='10', nullable=False))
    op.add_column('configuracion_incubadora', sa.Column('meses_recuperacion_max', sa.Integer(), server_default='36', nullable=False))
    op.add_column('configuracion_incubadora', sa.Column('plantillas_ruta', sa.JSON(), server_default=sa.text("'{}'"), nullable=False))
    op.create_check_constraint('ck_inc_margen', 'configuracion_incubadora', 'margen_minimo BETWEEN 0 AND 100')
    op.create_check_constraint('ck_inc_recuperacion', 'configuracion_incubadora', 'meses_recuperacion_max BETWEEN 1 AND 600')

    op.create_table(
        'rutas_emprendedoras',
        sa.Column('proyecto_id', sa.UUID(), nullable=False),
        sa.Column('tipo_proyecto', sa.String(20), nullable=True),
        sa.Column('tipo_propuesto', sa.String(20), nullable=True),
        sa.Column('clasificacion_confirmada', sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column('respuestas_clasificacion', sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('razon_clasificacion', sa.String(3000), server_default='', nullable=False),
        sa.Column('datos', sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('pasos', sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('formalizacion', sa.JSON(), server_default=sa.text("'{}'"), nullable=False),
        sa.Column('estado', sa.String(40), server_default='Registrado', nullable=False),
        sa.Column('version', sa.Integer(), server_default='0', nullable=False),
        sa.Column('historial', sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('actualizado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('Registrado','Diagnóstico','Revisión económica','En desarrollo','En validación','En validación tecnológica','En formalización','En operación','Canalizado','Pausado','Abandonado','Concluido')", name='ck_ruta_estado'),
        sa.CheckConstraint("tipo_proyecto IS NULL OR tipo_proyecto IN ('normal','tecnologica','no_seguro')", name='ck_ruta_tipo'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('proyecto_id'),
    )

    op.create_table(
        'calculos_economicos',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('proyecto_id', sa.UUID(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('entradas', sa.JSON(), nullable=False),
        sa.Column('resultados', sa.JSON(), nullable=False),
        sa.Column('semaforo', sa.String(12), nullable=False),
        sa.Column('creado_por', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('version >= 1', name='ck_calculo_version'),
        sa.CheckConstraint("semaforo IN ('rojo','amarillo','verde')", name='ck_calculo_semaforo'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_calculos_economicos_proyecto_id', 'calculos_economicos', ['proyecto_id'])

    op.create_table(
        'tareas_ruta_emprendedora',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('proyecto_id', sa.UUID(), nullable=False),
        sa.Column('paso_codigo', sa.String(12), server_default='', nullable=False),
        sa.Column('nombre', sa.String(160), nullable=False),
        sa.Column('descripcion', sa.String(3000), server_default='', nullable=False),
        sa.Column('responsable_id', sa.UUID(), nullable=False),
        sa.Column('fecha_objetivo', sa.Date(), nullable=False),
        sa.Column('evidencia_esperada', sa.String(1000), nullable=False),
        sa.Column('estado', sa.String(20), server_default='Pendiente', nullable=False),
        sa.Column('evidencia_texto', sa.String(3000), server_default='', nullable=False),
        sa.Column('evidencia_url', sa.String(2000), server_default='', nullable=False),
        sa.Column('documento_id', sa.UUID(), nullable=True),
        sa.Column('estado_evidencia', sa.String(30), server_default='No enviada', nullable=False),
        sa.Column('revision_notas', sa.String(3000), server_default='', nullable=False),
        sa.Column('revisado_por', sa.UUID(), nullable=True),
        sa.Column('version', sa.Integer(), server_default='0', nullable=False),
        sa.Column('historial', sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('creado_por', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('Pendiente','En proceso','Completada','Cancelada')", name='ck_tarea_ruta_estado'),
        sa.CheckConstraint("estado_evidencia IN ('No enviada','Pendiente de revisión','Aprobada','Corrección requerida')", name='ck_tarea_ruta_evidencia'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['responsable_id'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id']),
        sa.ForeignKeyConstraint(['revisado_por'], ['usuarios.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tareas_ruta_emprendedora_proyecto_id', 'tareas_ruta_emprendedora', ['proyecto_id'])
    op.create_index('ix_tareas_ruta_emprendedora_responsable_id', 'tareas_ruta_emprendedora', ['responsable_id'])
    op.create_index('ix_tareas_ruta_emprendedora_fecha_objetivo', 'tareas_ruta_emprendedora', ['fecha_objetivo'])

    op.create_table(
        'canalizaciones_ruta_emprendedora',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('proyecto_id', sa.UUID(), nullable=False),
        sa.Column('paso_codigo', sa.String(12), server_default='', nullable=False),
        sa.Column('necesidad', sa.String(1000), nullable=False),
        sa.Column('motivo', sa.String(3000), nullable=False),
        sa.Column('destino', sa.String(300), nullable=False),
        sa.Column('informacion_usuario', sa.String(3000), nullable=False),
        sa.Column('resultado_esperado', sa.String(2000), nullable=False),
        sa.Column('fecha_objetivo', sa.Date(), nullable=False),
        sa.Column('evidencia_url', sa.String(2000), server_default='', nullable=False),
        sa.Column('documento_id', sa.UUID(), nullable=True),
        sa.Column('resultado', sa.String(3000), server_default='', nullable=False),
        sa.Column('siguiente_accion', sa.String(3000), server_default='', nullable=False),
        sa.Column('motivo_cancelacion', sa.String(3000), server_default='', nullable=False),
        sa.Column('estado', sa.String(20), server_default='Abierta', nullable=False),
        sa.Column('version', sa.Integer(), server_default='0', nullable=False),
        sa.Column('historial', sa.JSON(), server_default=sa.text("'[]'"), nullable=False),
        sa.Column('creado_por', sa.UUID(), nullable=False),
        sa.Column('creado_en', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("estado IN ('Abierta','Cerrada','Cancelada')", name='ck_canalizacion_ruta_estado'),
        sa.CheckConstraint("estado != 'Cerrada' OR (length(btrim(resultado)) > 0 AND length(btrim(siguiente_accion)) > 0)", name='ck_canalizacion_ruta_cierre'),
        sa.CheckConstraint("estado != 'Cancelada' OR length(btrim(motivo_cancelacion)) > 0", name='ck_canalizacion_ruta_cancelacion'),
        sa.ForeignKeyConstraint(['proyecto_id'], ['proyectos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id']),
        sa.ForeignKeyConstraint(['creado_por'], ['usuarios.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_canalizaciones_ruta_emprendedora_proyecto_id', 'canalizaciones_ruta_emprendedora', ['proyecto_id'])
    op.create_index('ix_canalizaciones_ruta_emprendedora_fecha_objetivo', 'canalizaciones_ruta_emprendedora', ['fecha_objetivo'])


def downgrade():
    connection = op.get_bind()
    for table in ('rutas_emprendedoras', 'calculos_economicos', 'tareas_ruta_emprendedora', 'canalizaciones_ruta_emprendedora'):
        if connection.scalar(sa.text(f'SELECT EXISTS (SELECT 1 FROM {table})')):
            raise RuntimeError('Conserva los expedientes y cálculos al revertir la aplicación.')
    customized = connection.scalar(sa.text("SELECT EXISTS (SELECT 1 FROM configuracion_incubadora WHERE margen_minimo <> 10 OR meses_recuperacion_max <> 36 OR plantillas_ruta::text <> '{}')"))
    if customized:
        raise RuntimeError('Conserva la configuración de la ruta al revertir la aplicación.')
    op.drop_column('atenciones_incubadora', 'evidencia_esperada')
    op.drop_index('ix_tareas_ruta_emprendedora_fecha_objetivo', table_name='tareas_ruta_emprendedora')
    op.drop_index('ix_tareas_ruta_emprendedora_responsable_id', table_name='tareas_ruta_emprendedora')
    op.drop_index('ix_tareas_ruta_emprendedora_proyecto_id', table_name='tareas_ruta_emprendedora')
    op.drop_table('tareas_ruta_emprendedora')
    op.drop_index('ix_calculos_economicos_proyecto_id', table_name='calculos_economicos')
    op.drop_table('calculos_economicos')
    op.drop_table('rutas_emprendedoras')
    op.drop_constraint('ck_inc_recuperacion', 'configuracion_incubadora', type_='check')
    op.drop_constraint('ck_inc_margen', 'configuracion_incubadora', type_='check')
    op.drop_column('configuracion_incubadora', 'plantillas_ruta')
    op.drop_column('configuracion_incubadora', 'meses_recuperacion_max')
    op.drop_column('configuracion_incubadora', 'margen_minimo')
    op.drop_index('ix_canalizaciones_ruta_emprendedora_fecha_objetivo', table_name='canalizaciones_ruta_emprendedora')
    op.drop_index('ix_canalizaciones_ruta_emprendedora_proyecto_id', table_name='canalizaciones_ruta_emprendedora')
    op.drop_table('canalizaciones_ruta_emprendedora')
