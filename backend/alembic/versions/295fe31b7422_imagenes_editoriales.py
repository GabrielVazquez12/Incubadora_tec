"""Galerías de noticias y eventos."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '295fe31b7422'
down_revision = '184ed20a6311'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('imagenes_editoriales',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('publicacion_id', UUID(as_uuid=True), sa.ForeignKey('publicaciones.id', ondelete='CASCADE')),
        sa.Column('evento_id', UUID(as_uuid=True), sa.ForeignKey('eventos.id', ondelete='CASCADE')),
        sa.Column('alt', sa.String(300), nullable=False),
        sa.Column('media_type', sa.String(30), nullable=False),
        sa.Column('bucket', sa.String(), nullable=False),
        sa.Column('clave_archivo', sa.String(), nullable=False),
        sa.Column('contenido', sa.LargeBinary()),
        sa.Column('creado_en', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint('(publicacion_id IS NOT NULL) <> (evento_id IS NOT NULL)', name='ck_imagen_un_destino'))
    op.create_index('ix_imagenes_editoriales_publicacion_id', 'imagenes_editoriales', ['publicacion_id'])
    op.create_index('ix_imagenes_editoriales_evento_id', 'imagenes_editoriales', ['evento_id'])


def downgrade():
    op.drop_table('imagenes_editoriales')
