"""Review and correction history for project documents."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "a75c42e1b543"
down_revision = "f64b31d0a432"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("documentos", sa.Column("estatus", sa.String(), nullable=False, server_default="Pendiente"))
    op.add_column("documentos", sa.Column("observaciones", sa.Text(), nullable=False, server_default=""))
    op.add_column("documentos", sa.Column("historial", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("documentos", sa.Column("vigente", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("documentos", sa.Column("reemplaza_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_documentos_reemplaza", "documentos", "documentos", ["reemplaza_id"], ["id"])


def downgrade():
    op.drop_constraint("fk_documentos_reemplaza", "documentos", type_="foreignkey")
    for column in ("reemplaza_id", "vigente", "historial", "observaciones", "estatus"):
        op.drop_column("documentos", column)
