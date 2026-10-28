from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, JSON, Boolean, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.portal import Identified


class Audited(Identified):
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class PiezaDifusion(Audited, Base):
    __tablename__ = 'piezas_difusion'
    __table_args__ = (CheckConstraint("canal IN ('Instagram','TikTok','WhatsApp','Facebook','docentes','coordinadores','salones')", name='ck_difusion_canal'), CheckConstraint("estado IN ('planeada','publicada')", name='ck_difusion_estado'), CheckConstraint("tipo IN ('publicacion','reel','historia','video','experiencia')", name='ck_difusion_tipo'),)
    titulo = Column(String(160), nullable=False)
    canal = Column(String(30), nullable=False, index=True)
    fecha = Column(Date, nullable=False, index=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)
    estado = Column(String(20), nullable=False)
    enlace = Column(String(2000), nullable=False, default='', server_default='')
    publicacion_id = Column(UUID(as_uuid=True), ForeignKey('publicaciones.id'), index=True)
    tipo = Column(String(20), nullable=False, default='publicacion', server_default='publicacion')
    visible = Column(Boolean, nullable=False, default=False, server_default='false')


class VisitaSalon(Audited, Base):
    __tablename__ = 'visitas_salon'
    __table_args__ = (CheckConstraint('asistentes BETWEEN 0 AND 10000', name='ck_visita_asistentes'),)
    grupo = Column(String(160), nullable=False)
    docente_coordinador = Column(String(160), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)
    asistentes = Column(Integer, nullable=False)
    resultado = Column(String(3000), nullable=False)


class PlantillaMensaje(Audited, Base):
    __tablename__ = 'plantillas_mensaje'
    __table_args__ = (CheckConstraint("publico IN ('alumnos','docentes')", name='ck_plantilla_publico'),)
    titulo = Column(String(160), nullable=False)
    publico = Column(String(20), nullable=False)
    contenido = Column(String(3000), nullable=False)
    activa = Column(Boolean, nullable=False, default=True, server_default='true')


class EnvioMensaje(Audited, Base):
    __tablename__ = 'envios_mensaje'
    __table_args__ = (CheckConstraint("canal IN ('Instagram','TikTok','WhatsApp','Facebook','docentes','coordinadores','salones')", name='ck_envio_canal'),)
    plantilla_id = Column(UUID(as_uuid=True), ForeignKey('plantillas_mensaje.id'), nullable=False, index=True)
    contenido = Column(String(3000), nullable=False)
    destinatario = Column(String(160), nullable=False)
    fecha = Column(Date, nullable=False, index=True)
    canal = Column(String(30), nullable=False)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)


class PreguntaFrecuente(Audited, Base):
    __tablename__ = 'preguntas_frecuentes'
    __table_args__ = (CheckConstraint("seccion IN ('incubadora','innovatec')", name='ck_faq_seccion'), CheckConstraint('orden BETWEEN 0 AND 10000', name='ck_faq_orden'),)
    seccion = Column(String(20), nullable=False, index=True)
    pregunta = Column(String(160), nullable=False)
    respuesta = Column(String(3000), nullable=False)
    orden = Column(Integer, nullable=False)
    activa = Column(Boolean, nullable=False, default=True, server_default='true')


class ConfiguracionEnlaces(Audited, Base):
    __tablename__ = 'configuracion_enlaces'
    __table_args__ = (CheckConstraint('singleton = 1', name='ck_enlaces_singleton'),)
    singleton = Column(Integer, nullable=False, default=1, server_default='1', unique=True)
    vinculacion = Column(String(10000), nullable=False, default='', server_default='')
    contactos = Column(JSON, nullable=False, default=dict, server_default='{}')


class ContactoInstitucional(Audited, Base):
    __tablename__ = 'contactos_institucionales'
    __table_args__ = (CheckConstraint("estado IN ('nuevo','atendido')", name='ck_contacto_estado'),)
    nombre = Column(String(160), nullable=False)
    correo = Column(String(254), nullable=False)
    telefono = Column(String(20), nullable=False, default='', server_default='')
    asunto = Column(String(160), nullable=False)
    mensaje = Column(String(3000), nullable=False)
    origen = Column(String(20), nullable=False)
    consentimiento = Column(JSON, nullable=False)
    estado = Column(String(20), nullable=False, default='nuevo', server_default='nuevo', index=True)
    nota = Column(String(3000), nullable=False, default='', server_default='')
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class FichaEvento(Audited, Base):
    __tablename__ = 'fichas_evento'
    titulo = Column(String(160), nullable=False)
    descripcion = Column(String(3000), nullable=False)
    lema = Column(String(300), nullable=False, default='', server_default='')
    lugar = Column(String(300), nullable=False, default='', server_default='')
    evento_id = Column(UUID(as_uuid=True), ForeignKey('eventos.id'), unique=True)
    publicada = Column(Boolean, nullable=False, default=False, server_default='false')
