"""Complementary access profiles; the legacy role enum is unchanged."""
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class PerfilAcceso(Base):
    __tablename__ = 'perfiles_acceso'
    __table_args__ = (CheckConstraint("perfil IN ('asesor','administrador','sin_perfil')", name='ck_perfil_acceso'),)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), primary_key=True)
    perfil = Column(String(20), nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class AuditoriaAcceso(Base):
    __tablename__ = 'auditoria_acceso'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    entidad = Column(String(100), nullable=False, index=True)
    registro_id = Column(String(100), nullable=False)
    operacion = Column(String(10), nullable=False)
    campos = Column(JSON, nullable=False)
    fecha = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
