import uuid
from sqlalchemy import Column, String, Text, Date, Boolean, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Publication(Base):
    __tablename__ = 'publicaciones'
    __table_args__ = (CheckConstraint("vence IS NULL OR vence >= fecha", name="ck_publicacion_fechas"), CheckConstraint("categoria IN ('Noticia', 'Convocatoria', 'Aviso')", name="ck_publicacion_categoria"))
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String(160), nullable=False)
    resumen = Column(String(500), nullable=False)
    contenido = Column(Text, nullable=False)
    categoria = Column(String(30), nullable=False)
    fecha = Column(Date, nullable=False)
    vence = Column(Date, nullable=True)
    publicada = Column(Boolean, nullable=False, default=False)
    destacada = Column(Boolean, nullable=False, default=False)
