"""Asistencia verificada y constancias de participación en eventos."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "073dc19b5210"
down_revision = "a75c42e1b543"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("inscripciones", sa.Column("asistio", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("inscripciones", sa.Column("asistencia_por", UUID(as_uuid=True), nullable=True))
    op.add_column("inscripciones", sa.Column("asistencia_fecha", sa.DateTime(timezone=True), nullable=True))
    op.create_foreign_key("fk_inscripcion_asistencia_usuario", "inscripciones", "usuarios", ["asistencia_por"], ["id"])


def downgrade():
    op.drop_constraint("fk_inscripcion_asistencia_usuario", "inscripciones", type_="foreignkey")
    op.drop_column("inscripciones", "asistencia_fecha")
    op.drop_column("inscripciones", "asistencia_por")
    op.drop_column("inscripciones", "asistio")
