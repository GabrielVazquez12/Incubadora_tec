"""Participación y seguimiento de los proyectos de la incubadora."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Text, UniqueConstraint, LargeBinary, func, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class IntegranteProyecto(Base):
    __tablename__ = "integrantes_proyecto"

    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), primary_key=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="integrantes")
    usuario = relationship("Usuario")


class Documento(Base):
    __tablename__ = "documentos"
    __table_args__ = (UniqueConstraint("bucket", "clave_archivo", name="uq_documentos_objeto"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contenido = Column(LargeBinary, nullable=True)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True)
    subido_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nombre = Column(String, nullable=False)
    tipo = Column(String, nullable=False)
    bucket = Column(String, nullable=False)
    clave_archivo = Column(String, nullable=False)
    estatus = Column(String, nullable=False, default="Pendiente", server_default="Pendiente")
    observaciones = Column(Text, nullable=False, default="", server_default="")
    historial = Column(JSON, nullable=False, default=list, server_default="[]")
    vigente = Column(Boolean, nullable=False, default=True, server_default="true")
    reemplaza_id = Column(UUID(as_uuid=True), ForeignKey("documentos.id"), nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="documentos")
    subido_por = relationship("Usuario")


class HistorialEstatus(Base):
    __tablename__ = "historial_estatus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False, index=True)
    cambiado_por_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    estatus_anterior = Column(String, nullable=True)
    estatus_nuevo = Column(String, nullable=False)
    comentario = Column(Text, nullable=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    proyecto = relationship("Proyecto", back_populates="historial_estatus")
    cambiado_por = relationship("Usuario")
