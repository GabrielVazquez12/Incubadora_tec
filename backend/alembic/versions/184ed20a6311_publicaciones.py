"""Boletín editorial público con programación y caducidad."""
from datetime import date
from uuid import uuid4
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = '184ed20a6311'
down_revision = '073dc19b5210'
branch_labels = None
depends_on = None


def upgrade():
    table = op.create_table('publicaciones',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('titulo', sa.String(160), nullable=False),
        sa.Column('resumen', sa.String(500), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('categoria', sa.String(30), nullable=False),
        sa.Column('fecha', sa.Date(), nullable=False),
        sa.Column('vence', sa.Date(), nullable=True),
        sa.Column('publicada', sa.Boolean(), nullable=False),
        sa.Column('destacada', sa.Boolean(), nullable=False))
    entries = [
        ('Tu proyecto, acompañado desde el primer paso', 'Conoce los servicios de la Incubadora ITS y comienza tu solicitud desde el portal.', 'La Incubadora ITS acompaña el desarrollo de proyectos con asesoría legal, administrativa y de financiamiento. Crea una cuenta, completa tu solicitud y consulta las observaciones de coordinación desde tu espacio personal.\n\nEl registro de una cuenta no implica la aprobación del proyecto. La solicitud y sus anexos pasan por revisión antes de ingresar al proceso de incubación.', True),
        ('Consulta la agenda de formación y emprendimiento', 'Los eventos activos se publican en la agenda del sitio. Accede al portal para consultar cupos e inscribirte.', 'La agenda pública reúne los eventos activos de la incubadora cuya fecha aún no ha concluido. Cada actividad muestra fecha, hora y modalidad.\n\nPara participar, inicia sesión y consulta la disponibilidad en el módulo Eventos. Las actividades sujetas a pago requieren que el servicio de cobro esté habilitado. La constancia se puede descargar cuando coordinación confirma tu asistencia.', False),
        ('Asesoría y seguimiento en un mismo espacio', 'Consulta el avance de tu proyecto y agenda tutorías en los horarios disponibles de coordinación.', 'Desde el portal puedes consultar tu proyecto, registrar avances y dar seguimiento a las tareas. Las tutorías se reservan según la disponibilidad publicada por coordinación.\n\nInicia sesión para consultar los horarios de tu cuenta y revisar tus sesiones confirmadas. Si todavía no tienes un proyecto aprobado, comienza por completar tu solicitud.', False),
    ]
    op.bulk_insert(table, [dict(id=uuid4(), titulo=t, resumen=r, contenido=c, categoria='Noticia', fecha=date(2026, 10, 6), vence=date(2026, 11, 6), publicada=True, destacada=d) for t, r, c, d in entries])


def downgrade():
    op.drop_table('publicaciones')
