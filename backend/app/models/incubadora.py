"""Additive institutional follow-up, referencing the existing project/registration."""
from sqlalchemy import Column, String, Integer, Date, DateTime, ForeignKey, JSON, Boolean, CheckConstraint, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from app.models.portal import Identified


class ConfiguracionIncubadora(Base):
    __tablename__ = 'configuracion_incubadora'
    __table_args__ = (CheckConstraint('id = 1', name='ck_inc_config_singleton'), CheckConstraint('dias_inactividad IS NULL OR dias_inactividad BETWEEN 1 AND 3650', name='ck_inc_inactividad'), CheckConstraint('margen_minimo BETWEEN 0 AND 100', name='ck_inc_margen'), CheckConstraint('meses_recuperacion_max BETWEEN 1 AND 600', name='ck_inc_recuperacion'),)
    id = Column(Integer, primary_key=True, default=1)
    dias_inactividad = Column(Integer)
    margen_minimo = Column(Numeric(5, 2), nullable=False, default=10, server_default='10')
    meses_recuperacion_max = Column(Integer, nullable=False, default=36, server_default='36')
    plantillas_ruta = Column(JSON, nullable=False, default=dict, server_default='{}')
    aviso_privacidad = Column(String(20000), nullable=False, default='', server_default='')
    aviso_aprobado = Column(Boolean, nullable=False, default=False, server_default='false')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class ServicioCatalogo(Identified, Base):
    __tablename__ = 'servicios_catalogo'
    __table_args__ = (CheckConstraint('etapa BETWEEN 1 AND 4', name='ck_servicio_etapa'), CheckConstraint('nivel BETWEEN 1 AND 3', name='ck_servicio_nivel'), CheckConstraint('orden BETWEEN 0 AND 10000', name='ck_servicio_orden'),)
    nombre = Column(String(160), nullable=False)
    etapa = Column(Integer, nullable=False, index=True)
    nivel = Column(Integer, nullable=False)
    objetivo = Column(String(3000), nullable=False)
    resultado_esperado = Column(String(3000), nullable=False)
    canalizacion = Column(String(3000), nullable=False, default='', server_default='')
    orden = Column(Integer, nullable=False, default=0, server_default='0')
    activo = Column(Boolean, nullable=False, default=True, server_default='true')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class HitoCatalogo(Identified, Base):
    __tablename__ = 'hitos_catalogo'
    __table_args__ = (CheckConstraint('orden BETWEEN 0 AND 10000', name='ck_hito_orden'),)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey('servicios_catalogo.id'), nullable=False, index=True)
    nombre = Column(String(160), nullable=False)
    orden = Column(Integer, nullable=False, default=0, server_default='0')
    activo = Column(Boolean, nullable=False, default=True, server_default='true')
    propuesta = Column(Boolean, nullable=False, default=True, server_default='true')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class DiagnosticoIncubadora(Identified, Base):
    __tablename__ = 'diagnosticos_incubadora'
    __table_args__ = (CheckConstraint('proyecto_id IS NOT NULL OR registro_id IS NOT NULL', name='ck_diagnostico_origen'),)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), unique=True)
    registro_id = Column(UUID(as_uuid=True), ForeignKey('registros_iniciales.id'), unique=True)
    usuario_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)
    datos = Column(JSON, nullable=False)
    consentimiento = Column(JSON, nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ExpedienteIncubadora(Identified, Base):
    __tablename__ = 'expedientes_incubadora'
    __table_args__ = (CheckConstraint("estado IN ('activo','en_seguimiento','pausado','concluido','formalizado')", name='ck_expediente_estado'), CheckConstraint("estado NOT IN ('pausado','concluido','formalizado') OR (length(btrim(motivo)) > 0 AND fecha_estado IS NOT NULL)", name='ck_expediente_cierre'),)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), nullable=False, unique=True)
    asesor_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), index=True)
    primer_contacto = Column(Date)
    estado = Column(String(30), nullable=False, default='activo', server_default='activo')
    motivo = Column(String(3000), nullable=False, default='', server_default='')
    fecha_estado = Column(Date)
    proxima_revision = Column(Date, index=True)
    ultimo_movimiento = Column(Date, nullable=False)
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class AtencionIncubadora(Identified, Base):
    __tablename__ = 'atenciones_incubadora'
    __table_args__ = (CheckConstraint("tipo IN ('diagnostico','asesoria','seguimiento','canalizacion','cierre','recuperacion')", name='ck_atencion_tipo'), CheckConstraint('length(btrim(actividad)) BETWEEN 1 AND 3000', name='ck_atencion_actividad'), CheckConstraint('fecha_revision >= fecha', name='ck_atencion_revision'),)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), nullable=False, index=True)
    fecha = Column(Date, nullable=False)
    tipo = Column(String(30), nullable=False)
    servicio_id = Column(UUID(as_uuid=True), ForeignKey('servicios_catalogo.id'), index=True)
    actividad = Column(String(3000), nullable=False)
    responsable_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha_revision = Column(Date, nullable=False, index=True)
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'))
    evidencia_url = Column(String(2000), nullable=False, default='', server_default='')
    resultado = Column(String(3000), nullable=False, default='', server_default='')
    siguiente_accion = Column(String(3000), nullable=False, default='', server_default='')
    evidencia_esperada = Column(String(1000), nullable=False, default='', server_default='')
    registrado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class ProyectoHito(Base):
    __tablename__ = 'proyecto_hitos'
    __table_args__ = (CheckConstraint("estado IN ('pendiente','en_curso','cumplido')", name='ck_proyecto_hito_estado'), CheckConstraint("estado != 'cumplido' OR fecha IS NOT NULL", name='ck_proyecto_hito_fecha'),)
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), primary_key=True)
    hito_id = Column(UUID(as_uuid=True), ForeignKey('hitos_catalogo.id'), primary_key=True)
    estado = Column(String(20), nullable=False)
    fecha = Column(Date)
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'))
    evidencia_url = Column(String(2000), nullable=False, default='', server_default='')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class CanalizacionIncubadora(Identified, Base):
    __tablename__ = 'canalizaciones_incubadora'
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id'), nullable=False, index=True)
    atencion_id = Column(UUID(as_uuid=True), ForeignKey('atenciones_incubadora.id'), nullable=False, unique=True)
    destino = Column(String(300), nullable=False)
    motivo = Column(String(3000), nullable=False)
    fecha = Column(Date, nullable=False)
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'))
    evidencia_url = Column(String(2000), nullable=False, default='', server_default='')
    resultado = Column(String(3000), nullable=False, default='', server_default='')
    version = Column(Integer, nullable=False, default=1, server_default='1')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')


class RutaEmprendedora(Base):
    """Current route state; each mutation keeps the previous snapshot in historial."""
    __tablename__ = 'rutas_emprendedoras'
    __table_args__ = (
        CheckConstraint("estado IN ('Registrado','Diagnóstico','Revisión económica','En desarrollo','En validación','En validación tecnológica','En formalización','En operación','Canalizado','Pausado','Abandonado','Concluido')", name='ck_ruta_estado'),
        CheckConstraint("tipo_proyecto IS NULL OR tipo_proyecto IN ('normal','tecnologica','no_seguro')", name='ck_ruta_tipo'),
    )
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id', ondelete='CASCADE'), primary_key=True)
    tipo_proyecto = Column(String(20))
    tipo_propuesto = Column(String(20))
    clasificacion_confirmada = Column(Boolean, nullable=False, default=False, server_default='false')
    respuestas_clasificacion = Column(JSON, nullable=False, default=dict, server_default='{}')
    razon_clasificacion = Column(String(3000), nullable=False, default='', server_default='')
    datos = Column(JSON, nullable=False, default=dict, server_default='{}')
    pasos = Column(JSON, nullable=False, default=dict, server_default='{}')
    formalizacion = Column(JSON, nullable=False, default=dict, server_default='{}')
    estado = Column(String(40), nullable=False, default='Registrado', server_default='Registrado')
    version = Column(Integer, nullable=False, default=0, server_default='0')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')
    actualizado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())


class CalculoEconomico(Identified, Base):
    __tablename__ = 'calculos_economicos'
    __table_args__ = (
        CheckConstraint('version >= 1', name='ck_calculo_version'),
        CheckConstraint("semaforo IN ('rojo','amarillo','verde')", name='ck_calculo_semaforo'),
    )
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    entradas = Column(JSON, nullable=False)
    resultados = Column(JSON, nullable=False)
    semaforo = Column(String(12), nullable=False)
    creado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TareaRutaEmprendedora(Identified, Base):
    __tablename__ = 'tareas_ruta_emprendedora'
    __table_args__ = (
        CheckConstraint("estado IN ('Pendiente','En proceso','Completada','Cancelada')", name='ck_tarea_ruta_estado'),
        CheckConstraint("estado_evidencia IN ('No enviada','Pendiente de revisión','Aprobada','Corrección requerida')", name='ck_tarea_ruta_evidencia'),
    )
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False, index=True)
    paso_codigo = Column(String(12), nullable=False, default='', server_default='')
    nombre = Column(String(160), nullable=False)
    descripcion = Column(String(3000), nullable=False, default='', server_default='')
    responsable_id = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False, index=True)
    fecha_objetivo = Column(Date, nullable=False, index=True)
    evidencia_esperada = Column(String(1000), nullable=False)
    estado = Column(String(20), nullable=False, default='Pendiente', server_default='Pendiente')
    evidencia_texto = Column(String(3000), nullable=False, default='', server_default='')
    evidencia_url = Column(String(2000), nullable=False, default='', server_default='')
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'))
    estado_evidencia = Column(String(30), nullable=False, default='No enviada', server_default='No enviada')
    revision_notas = Column(String(3000), nullable=False, default='', server_default='')
    revisado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'))
    version = Column(Integer, nullable=False, default=0, server_default='0')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')
    creado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class CanalizacionRutaEmprendedora(Identified, Base):
    __tablename__ = 'canalizaciones_ruta_emprendedora'
    __table_args__ = (
        CheckConstraint("estado IN ('Abierta','Cerrada','Cancelada')", name='ck_canalizacion_ruta_estado'),
        CheckConstraint("estado != 'Cerrada' OR (length(btrim(resultado)) > 0 AND length(btrim(siguiente_accion)) > 0)", name='ck_canalizacion_ruta_cierre'),
        CheckConstraint("estado != 'Cancelada' OR length(btrim(motivo_cancelacion)) > 0", name='ck_canalizacion_ruta_cancelacion'),
    )
    proyecto_id = Column(UUID(as_uuid=True), ForeignKey('proyectos.id', ondelete='CASCADE'), nullable=False, index=True)
    paso_codigo = Column(String(12), nullable=False, default='', server_default='')
    necesidad = Column(String(1000), nullable=False)
    motivo = Column(String(3000), nullable=False)
    destino = Column(String(300), nullable=False)
    informacion_usuario = Column(String(3000), nullable=False)
    resultado_esperado = Column(String(2000), nullable=False)
    fecha_objetivo = Column(Date, nullable=False, index=True)
    evidencia_url = Column(String(2000), nullable=False, default='', server_default='')
    documento_id = Column(UUID(as_uuid=True), ForeignKey('documentos.id'))
    resultado = Column(String(3000), nullable=False, default='', server_default='')
    siguiente_accion = Column(String(3000), nullable=False, default='', server_default='')
    motivo_cancelacion = Column(String(3000), nullable=False, default='', server_default='')
    estado = Column(String(20), nullable=False, default='Abierta', server_default='Abierta')
    version = Column(Integer, nullable=False, default=0, server_default='0')
    historial = Column(JSON, nullable=False, default=list, server_default='[]')
    creado_por = Column(UUID(as_uuid=True), ForeignKey('usuarios.id'), nullable=False)
    creado_en = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
