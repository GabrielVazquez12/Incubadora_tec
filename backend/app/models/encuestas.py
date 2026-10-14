from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.portal import Identified


class Encuesta(Identified, Base):
    __tablename__ = 'encuestas'
    __table_args__ = (CheckConstraint("publico IN ('alumnos','docentes','usuarios de la Incubadora')", name='ck_encuesta_publico'), CheckConstraint('apertura IS NULL OR cierre IS NULL OR cierre >= apertura', name='ck_encuesta_fechas'), CheckConstraint('NOT publicada OR (apertura IS NOT NULL AND cierre IS NOT NULL)', name='ck_encuesta_publicacion'),)
    titulo = Column(String(160), nullable=False)
    descripcion = Column(String(3000), nullable=False)
    publico = Column(String(40), nullable=False)
    anonima = Column(Boolean, nullable=False, default=True, server_default='true')
    publicada = Column(Boolean, nullable=False, default=False, server_default='false', index=True)
    apertura = Column(Date)
    cierre = Column(Date)
    privacidad = Column(JSON, nullable=False, default=dict, server_default='{}')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class PreguntaEncuesta(Identified, Base):
    __tablename__ = 'preguntas_encuesta'
    encuesta_id = Column(UUID(as_uuid=True), ForeignKey('encuestas.id'), nullable=False, index=True)
    datos = Column(JSON, nullable=False)
    orden = Column(Integer, nullable=False)
    activa = Column(Boolean, nullable=False, default=True, server_default='true')


class RespuestaEncuesta(Identified, Base):
    __tablename__ = 'respuestas_encuesta'
    __table_args__ = (UniqueConstraint('encuesta_id', 'identidad', name='uq_respuesta_encuesta_identidad'),)
    encuesta_id = Column(UUID(as_uuid=True), ForeignKey('encuestas.id'), nullable=False, index=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), index=True)
    identidad = Column(String(64), nullable=False)
    datos = Column(JSON, nullable=False)
    consentimiento = Column(JSON, nullable=False, default=dict, server_default='{}')
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
