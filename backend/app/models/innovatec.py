"""Additive local InnovaTec workflow linked to existing proposals and events."""
from sqlalchemy import Column, String, Integer, Boolean, Date, DateTime, JSON, ForeignKey, UniqueConstraint, CheckConstraint, LargeBinary, func, Index, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.portal import Identified


class ConvocatoriaInnovaTec(Identified, Base):
    __tablename__ = "convocatorias_innovatec"
    __table_args__ = (CheckConstraint("anio BETWEEN 2000 AND 2100", name="ck_innova_conv_anio"),)
    anio = Column(Integer, unique=True, nullable=False)
    datos = Column(JSON, nullable=False, default=dict)
    publicada = Column(Boolean, nullable=False, default=False, server_default="false")
    version = Column(Integer, nullable=False, default=1, server_default="1")
    historial = Column(JSON, nullable=False, default=list, server_default="[]")


class ArchivoConvocatoriaInnovaTec(Identified, Base):
    __tablename__ = "archivos_convocatoria_innovatec"
    __table_args__ = (CheckConstraint("tipo IN ('convocatoria','manual','anexo')", name="ck_innova_archivo_tipo"),)
    convocatoria_id = Column(UUID(as_uuid=True), ForeignKey("convocatorias_innovatec.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    version_manual = Column(String(160), nullable=False, default="", server_default="")
    nombre = Column(String(240), nullable=False)
    mime = Column(String(160), nullable=False)
    bucket = Column(String, nullable=False)
    clave = Column(String, nullable=False)
    contenido = Column(LargeBinary, nullable=True)
    vigente = Column(Boolean, nullable=False, default=True, server_default="true")


class EquipoInnovaTec(Identified, Base):
    __tablename__ = "equipos_innovatec"
    __table_args__ = (CheckConstraint("estado IN ('inscrito','documentacion_recibida','etapa_local','acreditado','etapa_regional','etapa_nacional','no_acreditado','baja')", name="ck_innova_equipo_estado"), CheckConstraint("version >= 1", name="ck_innova_equipo_version"))
    innovacion_id = Column(UUID(as_uuid=True), ForeignKey("innovacion.id"), nullable=False, unique=True)
    convocatoria_id = Column(UUID(as_uuid=True), ForeignKey("convocatorias_innovatec.id"), nullable=False, index=True)
    folio = Column(String(80), nullable=False, unique=True)
    estado = Column(String(30), nullable=False, default="inscrito", server_default="inscrito", index=True)
    version = Column(Integer, nullable=False, default=1, server_default="1")
    consentimiento = Column(JSON, nullable=False)
    historial = Column(JSON, nullable=False, default=list, server_default="[]")
    seguimiento = Column(JSON, nullable=False, default=dict, server_default="{}")
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey("proyectos.id"), nullable=True, unique=True)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class IntegranteInnovaTec(Identified, Base):
    __tablename__ = "integrantes_innovatec"
    __table_args__ = (UniqueConstraint("equipo_id", "correo", name="uq_innova_integrante_correo"), CheckConstraint("tipo IN ('participante','asesor')", name="ck_innova_integrante_tipo"), CheckConstraint("semestre IS NULL OR semestre BETWEEN 1 AND 20", name="ck_innova_integrante_semestre"), CheckConstraint("diploma_estado IN ('pendiente','generado','entregado')", name="ck_innova_diploma_estado"), CheckConstraint("(diploma_estado = 'entregado') = (diploma_fecha IS NOT NULL)", name="ck_innova_diploma_fecha"))
    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos_innovatec.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(160), nullable=False)
    correo = Column(String(254), nullable=False)
    carrera = Column(String(160), nullable=False, default="", server_default="")
    semestre = Column(Integer, nullable=True)
    tipo = Column(String(20), nullable=False)
    diploma_estado = Column(String(20), nullable=False, default="pendiente", server_default="pendiente")
    diploma_fecha = Column(Date, nullable=True)
    vigente = Column(Boolean, nullable=False, default=True, server_default="true")


class DocumentoInnovaTec(Identified, Base):
    __tablename__ = "documentos_innovatec"
    __table_args__ = (CheckConstraint("estado IN ('recibido','observado','aprobado')", name="ck_innova_documento_estado"), Index("uq_innova_documento_vigente", "equipo_id", "requisito", unique=True, postgresql_where=text("vigente")))
    equipo_id = Column(UUID(as_uuid=True), ForeignKey("equipos_innovatec.id", ondelete="CASCADE"), nullable=False, index=True)
    requisito = Column(String(160), nullable=False)
    nombre = Column(String(240), nullable=False)
    mime = Column(String(160), nullable=False)
    bucket = Column(String, nullable=False)
    clave = Column(String, nullable=False)
    contenido = Column(LargeBinary, nullable=True)
    estado = Column(String(20), nullable=False, default="recibido", server_default="recibido")
    comentarios = Column(String(3000), nullable=False, default="", server_default="")
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    vigente = Column(Boolean, nullable=False, default=True, server_default="true")


class PlaticaInnovaTec(Identified, Base):
    __tablename__ = "platicas_innovatec"
    __table_args__ = (CheckConstraint("publico IN ('alumnos','docentes')", name="ck_innova_platica_publico"),)
    evento_id = Column(UUID(as_uuid=True), ForeignKey("eventos.id"), nullable=False, unique=True)
    publico = Column(String(20), nullable=False)
    contenido = Column(String(10000), nullable=False)
    sede = Column(String(300), nullable=False, default="", server_default="")
