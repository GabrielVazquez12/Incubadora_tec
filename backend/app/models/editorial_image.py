import uuid
from sqlalchemy import Column, String, ForeignKey, LargeBinary, DateTime, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import deferred
from app.database import Base


class EditorialImage(Base):
    __tablename__ = 'imagenes_editoriales'
    __table_args__ = (CheckConstraint('(publicacion_id IS NOT NULL) <> (evento_id IS NOT NULL)', name='ck_imagen_un_destino'),)
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    publicacion_id = Column(UUID(as_uuid=True), ForeignKey('publicaciones.id', ondelete='CASCADE'), index=True)
    evento_id = Column(UUID(as_uuid=True), ForeignKey('eventos.id', ondelete='CASCADE'), index=True)
    alt = Column(String(300), nullable=False)
    media_type = Column(String(30), nullable=False)
    bucket = Column(String, nullable=False)
    clave_archivo = Column(String, nullable=False)
    contenido = deferred(Column(LargeBinary))
    creado_en = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
