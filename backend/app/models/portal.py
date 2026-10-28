"""Entidades persistentes de los módulos del portal."""
import uuid
from sqlalchemy import Column, String, Integer, Date, Time, Numeric, ForeignKey, UniqueConstraint, JSON, Boolean, DateTime, CheckConstraint, Index, func, column, text
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Identified:
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class Avance(Identified, Base):
    __tablename__ = "avances"
    project = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    hito = Column(String, nullable=False)
    notas = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)


class Tarea(Identified, Base):
    __tablename__ = "tareas"
    __table_args__ = (CheckConstraint("estatus IN ('Pendiente', 'Completado')", name="ck_tarea_estatus"), CheckConstraint("length(btrim(nombre)) BETWEEN 1 AND 160", name="ck_tarea_nombre"))
    project = Column(UUID(as_uuid=True), ForeignKey("proyectos.id", ondelete="CASCADE"), nullable=False)
    nombre = Column(String, nullable=False)
    estatus = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)


class TipoEvento(Base):
    __tablename__ = "tipos_evento"
    __table_args__ = (Index("uq_tipos_evento_normalizado", func.lower(func.btrim(column("nombre"))), unique=True),)
    nombre = Column(String, primary_key=True)


class Evento(Identified, Base):
    __tablename__ = "eventos"
    __table_args__ = (CheckConstraint("cupo BETWEEN 1 AND 10000", name="ck_evento_cupo"), CheckConstraint("precio BETWEEN 0 AND 100000", name="ck_evento_precio"), CheckConstraint("modalidad IN ('Presencial', 'En línea', 'Híbrida')", name="ck_evento_modalidad"), CheckConstraint("estatus IN ('Activo', 'Pendiente', 'Inactivo')", name="ck_evento_estatus"))
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    tipo = Column(String, ForeignKey("tipos_evento.nombre"), nullable=False)
    fecha = Column(Date, nullable=False)
    hora = Column(Time, nullable=False)
    cupo = Column(Integer, nullable=False)
    precio = Column(Numeric(12, 2), nullable=False)
    modalidad = Column(String, nullable=False)
    estatus = Column(String, nullable=False)


class Inscripcion(Identified, Base):
    __tablename__ = "inscripciones"
    __table_args__ = (UniqueConstraint("event", "user", name="uq_inscripcion_evento_usuario"),)
    event = Column(UUID(as_uuid=True), ForeignKey("eventos.id"), nullable=False)
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estatus = Column(String, nullable=False)
    asistio = Column(Boolean, nullable=False, default=False, server_default="false")
    asistencia_por = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    asistencia_fecha = Column(DateTime(timezone=True), nullable=True)


class Pago(Identified, Base):
    __tablename__ = "pagos"
    event = Column(UUID(as_uuid=True), ForeignKey("eventos.id"), nullable=False)
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    importe = Column(Numeric(12, 2), nullable=False)
    estatus = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    modo = Column(String, nullable=False, default="prueba", server_default="prueba")


class Horario(Identified, Base):
    __tablename__ = "horarios"
    __table_args__ = (CheckConstraint("fin > inicio", name="ck_horario_intervalo"),)
    fecha = Column(Date, nullable=False)
    inicio = Column(Time, nullable=False)
    fin = Column(Time, nullable=False)
    coordinador = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)


class Tutoria(Identified, Base):
    __tablename__ = "tutorias"
    __table_args__ = (Index("uq_tutoria_confirmada_slot", "slot", unique=True, postgresql_where=text("estatus = 'Confirmada'")), CheckConstraint("estatus IN ('Confirmada', 'Completado', 'Cancelada')", name="ck_tutoria_estatus"))
    slot = Column(UUID(as_uuid=True), ForeignKey("horarios.id"), nullable=False)
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    estatus = Column(String, nullable=False)


class Solicitud(Identified, Base):
    __tablename__ = "solicitudes"
    registro_id = Column(UUID(as_uuid=True), ForeignKey("registros_iniciales.id"), nullable=True, unique=True)
    producto_servicio = Column(String, nullable=False, default="", server_default="")
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False, unique=True)
    nombre = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    especialidad = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    estatus = Column(String, nullable=False)


class Innovacion(Identified, Base):
    __tablename__ = "innovacion"
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    datos = Column(JSON, nullable=False)


class RegistroInicial(Identified, Base):
    __tablename__ = "registros_iniciales"
    user = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=False)
    datos = Column(JSON, nullable=False, default=dict)
    administracion = Column(JSON, nullable=False, default=dict)
    archivos = Column(JSON, nullable=False, default=dict)
    estatus = Column(String, nullable=False, default="Borrador")
    observaciones = Column(String, nullable=False, default="", server_default="")
    historial = Column(JSON, nullable=False, default=list, server_default="[]")
