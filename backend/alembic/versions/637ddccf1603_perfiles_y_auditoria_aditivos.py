"""Perfiles complementarios y auditoria transaccional aditivos."""
from alembic import op
import sqlalchemy as sa
revision = '637ddccf1603'
down_revision = '526ccbbe0502'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('perfiles_acceso', sa.Column('usuario_id', sa.UUID(), sa.ForeignKey('usuarios.id'), primary_key=True), sa.Column('perfil', sa.String(20), nullable=False), sa.Column('version', sa.Integer(), server_default='1', nullable=False), sa.Column('historial', sa.JSON(), server_default='[]', nullable=False), sa.CheckConstraint("perfil IN ('asesor','administrador','sin_perfil')", name='ck_perfil_acceso'))
    op.create_table('auditoria_acceso', sa.Column('id', sa.UUID(), primary_key=True), sa.Column('actor_id', sa.UUID(), nullable=False), sa.Column('entidad', sa.String(100), nullable=False), sa.Column('registro_id', sa.String(100), nullable=False), sa.Column('operacion', sa.String(10), nullable=False), sa.Column('campos', sa.JSON(), nullable=False), sa.Column('fecha', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()))
    for field in ('actor_id', 'entidad', 'fecha'):
        op.create_index(f'ix_auditoria_acceso_{field}', 'auditoria_acceso', [field])


def downgrade():
    connection = op.get_bind()
    for table in ('perfiles_acceso', 'auditoria_acceso'):
        if connection.scalar(sa.text(f'SELECT EXISTS (SELECT 1 FROM {table})')):
            raise RuntimeError('Conserva perfiles y auditoría con datos al revertir la aplicación.')
    op.drop_table('auditoria_acceso')
    op.drop_table('perfiles_acceso')
