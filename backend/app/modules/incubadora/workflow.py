"""Server-authoritative business route for Incubadora projects."""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP, ROUND_CEILING
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.access import assigned, advisor_project
from app.auth.security import get_current_user
from app.database import get_db
from app.models import (
    Usuario, Proyecto, Documento, ConfiguracionIncubadora, RutaEmprendedora,
    CalculoEconomico, TareaRutaEmprendedora, CanalizacionRutaEmprendedora,
    ExpedienteIncubadora,
)
from app.modules.compartido.services import (
    admin, fail, record, project_access, serialized, today,
)
from app.modules.incubadora.services import responsible
from app.modules.innovacion.services import audit, check_version
from app.schemas.ruta_emprendedora import (
    CalculadoraInput, ClasificacionInput, DatosRutaInput, PasoRutaInput,
    TareaRutaCrear, TareaRutaActualizar, RevisionTareaRuta,
    CanalizacionRutaCrear, CanalizacionRutaActualizar, EstadoRutaInput,
    ConfigRutaInput,
)

router = APIRouter(prefix='/portal/incubadora', tags=['Ruta emprendedora'])

DEFAULT_ROUTES = {
    'normal': [
        {'codigo': 'N1', 'titulo': 'Problema, solución y propuesta de valor', 'criterio_salida': 'Problema y propuesta descritos en una frase verificable.', 'orden': 1, 'obligatorio': True, 'activo': True},
        {'codigo': 'N2', 'titulo': 'Cliente y mercado', 'criterio_salida': 'Segmento prioritario y principales alternativas identificadas.', 'orden': 2, 'obligatorio': True, 'activo': True},
        {'codigo': 'N3', 'titulo': 'Modelo de negocio', 'criterio_salida': 'Forma de generar ingresos y recursos o actividades básicas definidas.', 'orden': 3, 'obligatorio': True, 'activo': True},
        {'codigo': 'N4', 'titulo': 'Validación comercial', 'criterio_salida': 'Evidencia inicial de entrevistas, prueba, preventa, piloto u otra validación.', 'orden': 4, 'obligatorio': True, 'activo': True},
        {'codigo': 'N5', 'titulo': 'Revisión económica', 'criterio_salida': 'Calculadora actualizada con supuestos posteriores a la validación.', 'orden': 5, 'obligatorio': True, 'activo': True},
        {'codigo': 'N6', 'titulo': 'Ventas y comercialización', 'criterio_salida': 'Canal, oferta, acción de prospección e indicador definidos.', 'orden': 6, 'obligatorio': True, 'activo': True},
        {'codigo': 'N7', 'titulo': 'Preparación para formalización', 'criterio_salida': 'Checklist mínimo listo para iniciar la ruta común.', 'orden': 7, 'obligatorio': True, 'activo': True},
    ],
    'tecnologica': [
        {'codigo': 'T1', 'titulo': 'Problema, aplicación y usuario', 'criterio_salida': 'Caso de uso prioritario definido.', 'orden': 1, 'obligatorio': True, 'activo': True},
        {'codigo': 'T2', 'titulo': 'Estado de desarrollo', 'criterio_salida': 'Clasificado como idea, prueba de concepto, prototipo, piloto o producto.', 'orden': 2, 'obligatorio': True, 'activo': True},
        {'codigo': 'T3', 'titulo': 'Validación técnica', 'criterio_salida': 'Prueba, responsable, criterio de éxito y evidencia definidos.', 'orden': 3, 'obligatorio': True, 'activo': True},
        {'codigo': 'T4', 'titulo': 'Validación comercial', 'criterio_salida': 'Hipótesis de cliente, prueba y resultado registrados.', 'orden': 4, 'obligatorio': True, 'activo': True},
        {'codigo': 'T5', 'titulo': 'Propiedad intelectual y confidencialidad', 'criterio_salida': 'Activos tecnológicos inventariados y decisión de canalización registrada.', 'orden': 5, 'obligatorio': True, 'activo': True},
        {'codigo': 'T6', 'titulo': 'Regulación y certificación', 'criterio_salida': 'Normas, permisos o certificaciones potenciales identificados; o “No aplica” justificado.', 'orden': 6, 'obligatorio': True, 'activo': True},
        {'codigo': 'T7', 'titulo': 'Modelo de negocio tecnológico', 'criterio_salida': 'Venta, servicio, licencia, suscripción, integración u otro modelo definido.', 'orden': 7, 'obligatorio': True, 'activo': True},
        {'codigo': 'T8', 'titulo': 'Escalamiento', 'criterio_salida': 'Brechas de producción, software, infraestructura, proveedores, soporte o talento registradas.', 'orden': 8, 'obligatorio': True, 'activo': True},
        {'codigo': 'T9', 'titulo': 'Financiamiento tecnológico', 'criterio_salida': 'Monto, destino y fuente definidos cuando aplique.', 'orden': 9, 'obligatorio': True, 'activo': True},
        {'codigo': 'T10', 'titulo': 'Preparación para formalización', 'criterio_salida': 'Proyecto listo para la ruta común o con canalización pendiente identificada.', 'orden': 10, 'obligatorio': True, 'activo': True},
    ],
    'comun': [
        {'codigo': 'F1', 'titulo': 'Identidad jurídica', 'criterio_salida': 'Ruta de persona física o moral, socios y dudas para especialista registrados.', 'orden': 1, 'obligatorio': True, 'activo': True},
        {'codigo': 'F2', 'titulo': 'Ruta fiscal', 'criterio_salida': 'RFC, facturación, obligaciones y medios electrónicos identificados; canalización cuando corresponda.', 'orden': 2, 'obligatorio': True, 'activo': True},
        {'codigo': 'F3', 'titulo': 'Marca y propiedad intelectual', 'criterio_salida': 'Decisión de revisión o protección y evidencia registradas.', 'orden': 3, 'obligatorio': True, 'activo': True},
        {'codigo': 'F4', 'titulo': 'Establecimiento', 'criterio_salida': 'Local físico y requisitos de uso, funcionamiento y protección civil revisados.', 'orden': 4, 'obligatorio': True, 'activo': True},
        {'codigo': 'F5', 'titulo': 'Trabajadores', 'criterio_salida': 'Contratación prevista y módulos laborales o de seguridad social identificados.', 'orden': 5, 'obligatorio': True, 'activo': True},
        {'codigo': 'F6', 'titulo': 'Datos personales', 'criterio_salida': 'Tratamiento de datos identificables y controles de privacidad identificados.', 'orden': 6, 'obligatorio': True, 'activo': True},
        {'codigo': 'F7', 'titulo': 'Requisitos sectoriales', 'criterio_salida': 'Autoridad u organismo identificado o “No aplica” justificado.', 'orden': 7, 'obligatorio': True, 'activo': True},
        {'codigo': 'F8', 'titulo': 'Cierre y siguiente revisión', 'criterio_salida': 'Pendientes, responsables, evidencias y decisión de cierre registrados.', 'orden': 8, 'obligatorio': True, 'activo': True},
    ],
}

ROUTE_STATES = {
    'Registrado': {'Diagnóstico', 'Revisión económica', 'Pausado', 'Abandonado'},
    'Diagnóstico': {'Revisión económica', 'En desarrollo', 'Pausado', 'Abandonado'},
    'Revisión económica': {'Diagnóstico', 'En desarrollo', 'Pausado', 'Abandonado'},
    'En desarrollo': {'En validación', 'En validación tecnológica', 'En formalización', 'Canalizado', 'Pausado', 'Abandonado'},
    'En validación': {'En desarrollo', 'En formalización', 'En operación', 'Canalizado', 'Pausado', 'Abandonado'},
    'En validación tecnológica': {'En desarrollo', 'En validación', 'En formalización', 'Canalizado', 'Pausado', 'Abandonado'},
    'En formalización': {'En operación', 'Canalizado', 'Concluido', 'Pausado', 'Abandonado'},
    'En operación': {'Concluido', 'Pausado', 'Abandonado'},
    'Canalizado': {'En desarrollo', 'En validación', 'En validación tecnológica', 'En formalización', 'Pausado'},
    'Pausado': {'Diagnóstico', 'Revisión económica', 'En desarrollo', 'En validación', 'En validación tecnológica', 'En formalización', 'En operación', 'Abandonado'},
    'Abandonado': {'Diagnóstico', 'En desarrollo'},
    'Concluido': {'En formalización', 'En operación'},
}

ROUTE_DATA_FIELDS = {
    'etapa_inicial', 'problema', 'solucion', 'propuesta_valor', 'cliente_objetivo', 'mercado',
    'alternativas', 'modelo_ingresos', 'recursos_actividades', 'evidencia_validacion',
    'canal_venta', 'oferta', 'indicador_ventas', 'estado_desarrollo', 'prueba_tecnica',
    'responsable_tecnico', 'criterio_exito', 'activos_tecnologicos', 'regulacion_potencial',
    'brechas_escalamiento', 'monto_financiamiento', 'destino_financiamiento', 'tiene_local',
    'contratara_personal',
}


def _route_templates(db):
    row = db.get(ConfiguracionIncubadora, 1)
    templates = row.plantillas_ruta if row and row.plantillas_ruta else DEFAULT_ROUTES
    return {kind: sorted([step for step in templates.get(kind, []) if step.get('activo', True)], key=lambda step: step.get('orden', 0)) for kind in DEFAULT_ROUTES}


def _active_steps(templates, kind):
    branch = templates.get(kind, []) if kind in ('normal', 'tecnologica') else []
    return [*branch, *templates.get('comun', [])]


def _project_steps(templates, kind, data):
    steps = _active_steps(templates, kind)
    if data.get('tiene_local') == 'no':
        steps = [step for step in steps if step['codigo'] != 'F4']
    if data.get('contratara_personal') == 'no':
        steps = [step for step in steps if step['codigo'] != 'F5']
    return steps


def _project_access(db, user, key):
    if assigned(db, user, key):
        return advisor_project(db, user, key)
    return project_access(db, user, key)


def _is_staff(db, user, key):
    return admin(user) or assigned(db, user, key)


def _require_staff(db, user, key):
    if not _is_staff(db, user, key):
        fail('Esta acción requiere coordinación o el asesor asignado.', 403)


def _require_open_route(route):
    if route.estado in ('Pausado', 'Abandonado', 'Concluido'):
        fail('Reabre el expediente antes de continuar con la ruta.', 409)


def _ensure_route(db, project_id):
    row = db.scalar(select(RutaEmprendedora).where(RutaEmprendedora.proyecto_id == project_id).with_for_update())
    if not row:
        row = RutaEmprendedora(proyecto_id=project_id, version=0, historial=[])
        db.add(row)
        db.flush()
    else:
        db.refresh(row)
    return row


def _snapshot(row):
    return {
        'tipo_proyecto': row.tipo_proyecto,
        'tipo_propuesto': row.tipo_propuesto,
        'clasificacion_confirmada': row.clasificacion_confirmada,
        'respuestas_clasificacion': row.respuestas_clasificacion or {},
        'razon_clasificacion': row.razon_clasificacion,
        'datos': row.datos or {}, 'pasos': row.pasos or {},
        'formalizacion': row.formalizacion or {}, 'estado': row.estado,
    }


def _audit(row, user, action, **details):
    row.historial = [*(row.historial or []), {
        'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id),
        'responsable': user.nombre, 'accion': action, **details,
    }]
    row.version = (row.version or 0) + 1
    row.actualizado_en = datetime.now(timezone.utc)


def _config_view(db):
    row = db.get(ConfiguracionIncubadora, 1)
    return {
        'margen_minimo': float(row.margen_minimo) if row else 10.0,
        'meses_recuperacion_max': row.meses_recuperacion_max if row else 36,
        'dias_inactividad': row.dias_inactividad if row else None,
        'plantillas_ruta': row.plantillas_ruta or DEFAULT_ROUTES if row else DEFAULT_ROUTES,
        'version': row.version if row else 0,
    }


def _task_counts(db, project_id):
    tasks = db.scalars(select(TareaRutaEmprendedora).where(TareaRutaEmprendedora.proyecto_id == project_id).order_by(TareaRutaEmprendedora.fecha_objetivo, TareaRutaEmprendedora.creado_en)).all()
    return [serialized(task) for task in tasks]


def _channelings(db, project_id):
    rows = db.scalars(select(CanalizacionRutaEmprendedora).where(CanalizacionRutaEmprendedora.proyecto_id == project_id).order_by(CanalizacionRutaEmprendedora.fecha_objetivo)).all()
    return [serialized(row) for row in rows]


def _calculations(db, project_id):
    rows = db.scalars(select(CalculoEconomico).where(CalculoEconomico.proyecto_id == project_id).order_by(CalculoEconomico.version.desc())).all()
    return [serialized(row) for row in rows]


def _route_view(db, project, row=None):
    templates = _route_templates(db)
    row = row or db.get(RutaEmprendedora, project.id)
    if row:
        result = serialized(row)
    else:
        result = {
            'proyecto_id': str(project.id), 'tipo_proyecto': None, 'tipo_propuesto': None,
            'clasificacion_confirmada': False, 'respuestas_clasificacion': {}, 'razon_clasificacion': '',
            'datos': {'etapa_inicial': 'idea'}, 'pasos': {}, 'formalizacion': {},
            'estado': 'Registrado', 'version': 0, 'historial': [],
        }
    result['proyecto'] = {
        'id': str(project.id), 'nombre': project.nombre, 'descripcion': project.descripcion,
        'producto_servicio': project.producto_servicio, 'usuario_id': str(project.usuario_id),
        'creado_en': project.creado_en.isoformat() if project.creado_en else None,
    }
    kind = result.get('tipo_proyecto') or result.get('tipo_propuesto')
    result['plantillas'] = _project_steps(templates, kind, result.get('datos') or {})
    result['plantillas_completas'] = templates
    result['calculadora'] = _calculations(db, project.id)
    result['tareas'] = _task_counts(db, project.id)
    result['canalizaciones_ruta'] = _channelings(db, project.id)
    result['parametros'] = _config_view(db)
    result['pasos_obligatorios'] = sum(1 for step in result['plantillas'] if step.get('obligatorio', True))
    return result


def _check_document(db, project_id, document_id):
    if document_id:
        document = record(db, Documento, document_id)
        if document.proyecto_id != project_id or not document.vigente:
            fail('La evidencia debe ser un documento vigente del mismo proyecto.', 422)


def _decimal(value):
    return Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate(inputs, margin_threshold=Decimal('10'), recovery_threshold=36):
    price = inputs.precio_venta
    quantity = Decimal(inputs.unidades_estimadas)
    fixed = inputs.costos_fijos
    variable_unit = inputs.costo_variable_unitario
    initial = inputs.inversion_inicial
    income = price * quantity
    variable_cost = variable_unit * quantity
    total_cost = fixed + variable_cost
    profit = income - total_cost
    contribution = price - variable_unit
    break_even = fixed / contribution if contribution > 0 else None
    margin = (profit / income * 100) if income > 0 else None
    recovery = initial / profit if profit > 0 else None
    break_even_units = int(break_even.to_integral_value(rounding=ROUND_CEILING)) if break_even is not None else None
    below_break_even = break_even_units is not None and inputs.unidades_estimadas < break_even_units
    if contribution <= 0 or profit <= 0 or below_break_even:
        light = 'rojo'
    elif margin is not None and (margin < margin_threshold or recovery is not None and recovery > recovery_threshold):
        light = 'amarillo'
    else:
        light = 'verde'
    causes = []
    if contribution <= 0:
        causes.append('El precio no cubre el costo variable unitario.')
    if profit <= 0:
        causes.append('La utilidad mensual estimada no es positiva.')
    if below_break_even:
        causes.append('El volumen estimado está por debajo del punto de equilibrio.')
    if light == 'amarillo':
        if margin is not None and margin < margin_threshold:
            causes.append(f'El margen es menor al umbral de {margin_threshold}% configurado.')
        if recovery is not None and recovery > recovery_threshold:
            causes.append(f'La recuperación supera {recovery_threshold} meses.')
    return {
        'ingreso_mensual': float(_decimal(income)),
        'costo_variable_mensual': float(_decimal(variable_cost)),
        'costo_total_mensual': float(_decimal(total_cost)),
        'utilidad_mensual': float(_decimal(profit)),
        'contribucion_unitaria': float(_decimal(contribution)),
        'punto_equilibrio_unidades': float(_decimal(break_even)) if break_even is not None else None,
        'unidades_equilibrio_redondeadas': break_even_units,
        'margen_porcentaje': float(_decimal(margin)) if margin is not None else None,
        'meses_recuperacion': float(_decimal(recovery)) if recovery is not None else None,
        'semaforo': light,
        'causas': causes,
        'nota': 'Estimación preliminar con los supuestos capturados; no sustituye un estudio financiero.',
    }


@router.get('/configuracion-ruta')
def route_config(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    from app.modules.compartido.services import require_admin
    require_admin(user)
    return _config_view(db)


@router.put('/configuracion-ruta')
def save_route_config(payload: ConfigRutaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    from app.modules.compartido.services import require_admin
    require_admin(user)
    record(db, Usuario, user.id, lock=True)
    row = db.scalar(select(ConfiguracionIncubadora).where(ConfiguracionIncubadora.id == 1).with_for_update())
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('La configuración no existe.', 404)
    else:
        row = ConfiguracionIncubadora(id=1, version=0, historial=[])
        db.add(row)
    before = {'margen_minimo': float(row.margen_minimo or 10) if row.margen_minimo is not None else 10, 'meses_recuperacion_max': row.meses_recuperacion_max or 36}
    row.margen_minimo = payload.margen_minimo
    row.meses_recuperacion_max = payload.meses_recuperacion_max
    row.dias_inactividad = payload.dias_inactividad
    row.plantillas_ruta = {key: [step.model_dump(mode='json') for step in steps] for key, steps in payload.plantillas_ruta.items()}
    row.historial = [*(row.historial or []), {'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'accion': 'configuracion_ruta', 'anterior': before}]
    row.version = (row.version or 0) + 1
    db.commit()
    return _config_view(db)


@router.get('/proyectos/{key}/ruta-emprendedora')
def get_route(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    return _route_view(db, project)


@router.put('/proyectos/{key}/ruta-emprendedora/datos')
def save_route_data(key: UUID, payload: DatosRutaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    invalid = set(payload.datos) - ROUTE_DATA_FIELDS
    if invalid:
        fail(f'Campos no reconocidos en la ruta: {", ".join(sorted(invalid))}.', 422)
    row = _ensure_route(db, project.id)
    _require_open_route(row)
    check_version(row, payload.version)
    previous = row.datos or {}
    row.datos = {**previous, **payload.datos}
    if row.estado == 'Registrado':
        row.estado = 'Diagnóstico'
    _audit(row, user, 'guardar_datos_ruta', campos=sorted(payload.datos), anterior=previous)
    db.commit()
    return _route_view(db, project, row)


@router.post('/proyectos/{key}/ruta-emprendedora/calculos', status_code=201)
def save_calculation(key: UUID, payload: CalculadoraInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    route = _ensure_route(db, project.id)
    _require_open_route(route)
    latest = db.scalar(select(func.max(CalculoEconomico.version)).where(CalculoEconomico.proyecto_id == project.id)) or 0
    row_config = db.get(ConfiguracionIncubadora, 1)
    margin_threshold = Decimal(str(row_config.margen_minimo if row_config else 10))
    recovery_threshold = row_config.meses_recuperacion_max if row_config else 36
    results = calculate(payload, margin_threshold, recovery_threshold)
    calculation = CalculoEconomico(
        id=uuid4(), proyecto_id=project.id, version=latest + 1,
        entradas=payload.model_dump(mode='json'), resultados=results,
        semaforo=results['semaforo'], creado_por=user.id,
    )
    db.add(calculation)
    previous = _snapshot(route)
    route.estado = 'Revisión económica'
    _audit(route, user, 'calculo_economico', version=latest + 1, semaforo=results['semaforo'], anterior=previous)
    folder = db.get(ExpedienteIncubadora, project.id)
    if folder:
        folder.ultimo_movimiento = today()
    db.commit()
    return {'calculo': serialized(calculation), 'ruta': _route_view(db, project, route)}


@router.put('/proyectos/{key}/ruta-emprendedora/clasificacion')
def save_classification(key: UUID, payload: ClasificacionInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    row = _ensure_route(db, project.id)
    _require_open_route(row)
    check_version(row, payload.version)
    if not db.scalar(select(CalculoEconomico.id).where(CalculoEconomico.proyecto_id == key).limit(1)):
        fail('Guarda primero el análisis económico para iniciar la clasificación.', 409)
    staff = _is_staff(db, user, key)
    answers = {
        'depende_tecnologia': payload.depende_tecnologia,
        'requiere_validacion_tecnica': payload.requiere_validacion_tecnica,
        'activo_protegible': payload.activo_protegible,
    }
    proposal = 'tecnologica' if sum(answers.values()) >= 2 else 'normal'
    if row.clasificacion_confirmada and not staff and (payload.tipo_proyecto != row.tipo_proyecto or answers != (row.respuestas_clasificacion or {})):
        fail('La clasificación ya está confirmada. Solicita al docente asignado que la cambie.', 403)
    if payload.tipo_proyecto == 'no_seguro':
        if not payload.razon.strip():
            fail('Describe la duda para abrir el diagnóstico corto.', 422)
        confirmed = False
    elif payload.tipo_proyecto != proposal and not staff:
        fail('La propuesta automática no coincide con tus respuestas. Solicita revisión docente para cambiarla.', 422)
    else:
        if payload.tipo_proyecto != proposal and not payload.razon.strip():
            fail('El cambio docente requiere una justificación.', 422)
        confirmed = staff
    previous = _snapshot(row)
    row.respuestas_clasificacion = answers
    row.tipo_propuesto = proposal
    row.tipo_proyecto = payload.tipo_proyecto
    row.clasificacion_confirmada = confirmed
    row.razon_clasificacion = payload.razon.strip()
    if row.estado == 'Registrado':
        row.estado = 'Diagnóstico'
    _audit(row, user, 'clasificacion', propuesta=proposal, tipo=payload.tipo_proyecto, confirmada=confirmed, razon=payload.razon.strip(), anterior=previous)
    db.commit()
    return _route_view(db, project, row)


@router.put('/proyectos/{key}/ruta-emprendedora/pasos/{codigo}')
def save_route_step(key: UUID, codigo: str, payload: PasoRutaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    route = _ensure_route(db, project.id)
    _require_open_route(route)
    check_version(route, payload.version)
    templates = _route_templates(db)
    kind = route.tipo_proyecto if route.tipo_proyecto in ('normal', 'tecnologica') else route.tipo_propuesto
    template = next((step for step in _project_steps(templates, kind, route.datos or {}) if step['codigo'] == codigo), None)
    if not template:
        fail('El paso no corresponde a la ruta vigente.', 404)
    staff = _is_staff(db, user, key)
    previous = (route.pasos or {}).get(codigo, {})
    if not staff and previous.get('estado') in ('completado', 'no_aplica'):
        fail('El paso ya fue revisado. Solicita al docente que lo reabra si hace falta.', 409)
    if staff and payload.estado == 'completado':
        submitted = next((entry for entry in reversed(previous.get('historial') or []) if entry.get('estado') == 'en_revision'), None)
        if submitted and submitted.get('usuario_id') == str(user.id):
            fail('Quien envió la evidencia no puede aprobar su propio paso.', 403)
    if payload.estado in ('completado', 'no_aplica') and not staff:
        fail('El docente debe aprobar el paso o justificar que no aplica.', 403)
    active_steps = _project_steps(templates, kind, route.datos or {})
    if payload.estado in ('completado', 'no_aplica'):
        if not route.clasificacion_confirmada or route.tipo_proyecto not in ('normal', 'tecnologica'):
            fail('Coordinación debe confirmar la clasificación antes de aprobar los pasos de la ruta.', 409)
        position = next(index for index, step in enumerate(active_steps) if step['codigo'] == codigo)
        pending_before = [step['codigo'] for step in active_steps[:position] if step.get('obligatorio', True) and (route.pasos or {}).get(step['codigo'], {}).get('estado') not in ('completado', 'no_aplica')]
        if pending_before and not payload.justificacion.strip():
            fail(f'Para avanzar antes de {", ".join(pending_before)}, registra una justificación docente.', 422)
    if payload.estado == 'no_aplica' and not payload.justificacion.strip():
        fail('Justifica por qué este paso no aplica.', 422)
    if payload.estado == 'en_revision' and not (payload.evidencia_texto.strip() or payload.evidencia_url or payload.documento_id):
        fail('Adjunta una evidencia antes de enviarla a revisión.', 422)
    if payload.estado == 'completado' and not (payload.evidencia_texto.strip() or payload.evidencia_url or payload.documento_id or payload.justificacion.strip()):
        fail('Para aprobar, registra evidencia o una justificación docente.', 422)
    if staff and payload.estado in ('completado', 'no_aplica'):
        latest = db.scalar(select(CalculoEconomico).where(CalculoEconomico.proyecto_id == key).order_by(CalculoEconomico.version.desc()).limit(1))
        if latest and latest.semaforo != 'verde' and not payload.justificacion.strip():
            fail('El semáforo económico no está en verde. Registra la autorización docente y su justificación.', 422)
    _check_document(db, project.id, payload.documento_id)
    before = _snapshot(route)
    steps = dict(route.pasos or {})
    previous = steps.get(codigo, {})
    steps[codigo] = {
        'estado': payload.estado, 'respuesta': payload.respuesta.strip(),
        'evidencia_texto': payload.evidencia_texto.strip(), 'evidencia_url': payload.evidencia_url,
        'documento_id': str(payload.documento_id) if payload.documento_id else None,
        'justificacion': payload.justificacion.strip(),
        'revisado_por': str(user.id) if payload.estado in ('completado', 'no_aplica') else previous.get('revisado_por'),
        'historial': [*(previous.get('historial') or []), {'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'estado': payload.estado, 'justificacion': payload.justificacion.strip()}],
    }
    route.pasos = steps
    if payload.estado in ('completado', 'no_aplica'):
        route.estado = 'En formalización' if codigo.startswith('F') else 'En validación tecnológica' if codigo.startswith('T') else 'En validación'
    elif route.estado in ('Registrado', 'Diagnóstico', 'Revisión económica'):
        route.estado = 'En desarrollo'
    _audit(route, user, 'paso_ruta', codigo=codigo, estado=payload.estado, anterior=before)
    db.commit()
    return _route_view(db, project, route)


@router.put('/proyectos/{key}/ruta-emprendedora/estado')
def update_route_state(key: UUID, payload: EstadoRutaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    _require_staff(db, user, key)
    route = _ensure_route(db, project.id)
    check_version(route, payload.version)
    if payload.estado not in ROUTE_STATES.get(route.estado, set()):
        fail('La transición de estado no está permitida.', 409)
    latest = db.scalar(select(CalculoEconomico).where(CalculoEconomico.proyecto_id == key).order_by(CalculoEconomico.version.desc()).limit(1))
    if latest and latest.semaforo != 'verde' and payload.estado in ('En desarrollo', 'En validación', 'En validación tecnológica', 'En formalización', 'En operación') and not payload.motivo.strip():
        fail('El semáforo económico no está en verde. Registra la autorización docente y su justificación.', 422)
    if payload.estado in ('Pausado', 'Abandonado') and not payload.motivo.strip():
        fail('Registra el motivo de la pausa o abandono.', 422)
    if payload.estado == 'Concluido':
        templates = _route_templates(db)
        kind = route.tipo_proyecto if route.tipo_proyecto in ('normal', 'tecnologica') else route.tipo_propuesto
        if (not route.clasificacion_confirmada or route.tipo_proyecto not in ('normal', 'tecnologica')) and not (payload.cierre_administrativo and admin(user) and payload.motivo.strip()):
            fail('Confirma la clasificación antes de concluir la ruta. El cierre administrativo requiere motivo.', 409)
        pending = [step['codigo'] for step in _project_steps(templates, kind, route.datos or {}) if step.get('obligatorio', True) and (route.pasos or {}).get(step['codigo'], {}).get('estado') not in ('completado', 'no_aplica')]
        pending_tasks = db.scalar(select(func.count()).select_from(TareaRutaEmprendedora).where(TareaRutaEmprendedora.proyecto_id == key, TareaRutaEmprendedora.estado.notin_(['Completada', 'Cancelada']))) or 0
        if (pending or pending_tasks) and not (payload.cierre_administrativo and admin(user) and payload.motivo.strip()):
            fail('No se puede concluir: hay pasos o tareas obligatorios pendientes. El cierre administrativo requiere motivo.', 409)
    if payload.cierre_administrativo and (not admin(user) or not payload.motivo.strip()):
        fail('El cierre administrativo requiere coordinación y motivo.', 403)
    previous = route.estado
    route.estado = payload.estado
    _audit(route, user, 'cambio_estado', anterior=previous, estado=payload.estado, motivo=payload.motivo.strip(), cierre_administrativo=payload.cierre_administrativo)
    db.commit()
    return _route_view(db, project, route)


@router.post('/proyectos/{key}/ruta-emprendedora/tareas', status_code=201)
def create_route_task(key: UUID, payload: TareaRutaCrear, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    _require_staff(db, user, key)
    if payload.fecha_objetivo < today():
        fail('La fecha objetivo debe ser hoy o posterior.', 422)
    responsible(db, project, payload.responsable_id)
    route = _ensure_route(db, project.id)
    _require_open_route(route)
    templates = _route_templates(db)
    kind = route.tipo_proyecto if route.tipo_proyecto in ('normal', 'tecnologica') else route.tipo_propuesto
    if payload.paso_codigo and not any(step['codigo'] == payload.paso_codigo for step in _project_steps(templates, kind, route.datos or {})):
        fail('El paso de la tarea no pertenece a la ruta del proyecto.', 422)
    row = TareaRutaEmprendedora(id=uuid4(), proyecto_id=project.id, paso_codigo=payload.paso_codigo, nombre=payload.nombre.strip(), descripcion=payload.descripcion.strip(), responsable_id=payload.responsable_id, fecha_objetivo=payload.fecha_objetivo, evidencia_esperada=payload.evidencia_esperada.strip(), creado_por=user.id, version=0, historial=[])
    db.add(row)
    _audit(route, user, 'tarea_asignada', tarea_id=str(row.id), nombre=row.nombre, responsable_id=str(row.responsable_id), fecha_objetivo=row.fecha_objetivo.isoformat())
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/ruta-emprendedora/tareas/{task_id}')
def update_route_task(key: UUID, task_id: UUID, payload: TareaRutaActualizar, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    task = record(db, TareaRutaEmprendedora, task_id, lock=True)
    if task.proyecto_id != project.id:
        fail('La tarea no pertenece al proyecto.', 404)
    staff = _is_staff(db, user, key)
    _require_open_route(_ensure_route(db, project.id))
    if not staff and task.responsable_id != user.id:
        fail('La tarea está asignada a otra persona.', 403)
    check_version(task, payload.version)
    _check_document(db, project.id, payload.documento_id)
    evidence_present = bool(payload.evidencia_texto.strip() or payload.evidencia_url or payload.documento_id)
    if not staff and payload.estado in ('Completada', 'Cancelada'):
        fail('El responsable envía la evidencia; el asesor aprueba o cancela la tarea.', 403)
    if payload.estado == 'Completada' and task.estado_evidencia != 'Aprobada':
        fail('La evidencia debe aprobarse antes de completar la tarea.', 409)
    if evidence_present:
        task.evidencia_texto = payload.evidencia_texto.strip()
        task.evidencia_url = payload.evidencia_url
        task.documento_id = payload.documento_id
        task.estado_evidencia = 'Pendiente de revisión'
        task.estado = 'En proceso' if not staff else payload.estado
        task.revisado_por = None
        task.revision_notas = ''
    else:
        task.estado = payload.estado
    task.version += 1
    task.historial = [*(task.historial or []), {'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'accion': 'evidencia_enviada' if evidence_present else 'estado', 'estado': task.estado}]
    db.commit()
    return serialized(task)


@router.put('/proyectos/{key}/ruta-emprendedora/tareas/{task_id}/revision')
def review_route_task(key: UUID, task_id: UUID, payload: RevisionTareaRuta, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    _require_staff(db, user, key)
    _require_open_route(_ensure_route(db, project.id))
    task = record(db, TareaRutaEmprendedora, task_id, lock=True)
    if task.proyecto_id != project.id:
        fail('La tarea no pertenece al proyecto.', 404)
    check_version(task, payload.version)
    if task.estado_evidencia != 'Pendiente de revisión':
        fail('La tarea no tiene evidencia pendiente de revisión.', 409)
    submitted = next((entry for entry in reversed(task.historial or []) if entry.get('accion') == 'evidencia_enviada'), None)
    if submitted and submitted.get('usuario_id') == str(user.id):
        fail('Quien envió la evidencia no puede aprobarla.', 403)
    task.estado_evidencia = payload.decision
    task.revision_notas = payload.notas.strip()
    task.revisado_por = user.id
    if payload.decision == 'Aprobada':
        task.estado = 'Completada'
    else:
        task.estado = 'En proceso'
    task.version += 1
    task.historial = [*(task.historial or []), {'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'accion': 'revision_evidencia', 'decision': payload.decision, 'notas': payload.notas.strip()}]
    db.commit()
    return serialized(task)


@router.post('/proyectos/{key}/ruta-emprendedora/canalizaciones', status_code=201)
def create_route_referral(key: UUID, payload: CanalizacionRutaCrear, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    _require_staff(db, user, key)
    if payload.fecha_objetivo < today():
        fail('La fecha objetivo debe ser hoy o posterior.', 422)
    _check_document(db, project.id, payload.documento_id)
    route = _ensure_route(db, project.id)
    _require_open_route(route)
    templates = _route_templates(db)
    kind = route.tipo_proyecto if route.tipo_proyecto in ('normal', 'tecnologica') else route.tipo_propuesto
    if payload.paso_codigo and not any(step['codigo'] == payload.paso_codigo for step in _project_steps(templates, kind, route.datos or {})):
        fail('El paso de la canalización no pertenece a la ruta.', 422)
    before = _snapshot(route)
    row = CanalizacionRutaEmprendedora(
        id=uuid4(), proyecto_id=project.id, paso_codigo=payload.paso_codigo,
        necesidad=payload.necesidad.strip(), motivo=payload.motivo.strip(), destino=payload.destino.strip(),
        informacion_usuario=payload.informacion_usuario.strip(), resultado_esperado=payload.resultado_esperado.strip(),
        fecha_objetivo=payload.fecha_objetivo, evidencia_url=payload.evidencia_url,
        documento_id=payload.documento_id, creado_por=user.id, version=0, historial=[],
    )
    db.add(row)
    row.historial = [{'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'accion': 'creada'}]
    route.estado = 'Canalizado'
    _audit(route, user, 'canalizacion_creada', canalizacion_id=str(row.id), anterior=before)
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/ruta-emprendedora/canalizaciones/{referral_id}')
def update_route_referral(key: UUID, referral_id: UUID, payload: CanalizacionRutaActualizar, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    _require_staff(db, user, key)
    referral = record(db, CanalizacionRutaEmprendedora, referral_id, lock=True)
    if referral.proyecto_id != project.id:
        fail('La canalización no pertenece al proyecto.', 404)
    check_version(referral, payload.version)
    if referral.estado != 'Abierta':
        fail('La canalización ya fue cerrada o cancelada.', 409)
    if payload.estado == 'Cerrada':
        if not (payload.evidencia_url or payload.documento_id):
            fail('Registra la evidencia de regreso antes de cerrar la canalización.', 422)
        _check_document(db, project.id, payload.documento_id)
    referral.resultado = payload.resultado.strip()
    referral.siguiente_accion = payload.siguiente_accion.strip()
    referral.estado = payload.estado
    referral.motivo_cancelacion = payload.motivo_cancelacion.strip()
    if payload.documento_id:
        referral.documento_id = payload.documento_id
    if payload.evidencia_url:
        referral.evidencia_url = payload.evidencia_url
    referral.version += 1
    referral.historial = [*(referral.historial or []), {'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id), 'responsable': user.nombre, 'estado': referral.estado, 'resultado': referral.resultado, 'siguiente_accion': referral.siguiente_accion, 'motivo_cancelacion': referral.motivo_cancelacion}]
    if payload.estado == 'Cerrada':
        route = _ensure_route(db, project.id)
        previous = _snapshot(route)
        if route.estado == 'Canalizado':
            route.estado = 'En formalización' if referral.paso_codigo.startswith('F') else 'En validación tecnológica' if referral.paso_codigo.startswith('T') else 'En desarrollo'
            _audit(route, user, 'canalizacion_cerrada', canalizacion_id=str(referral.id), resultado=referral.resultado, siguiente_accion=referral.siguiente_accion, anterior=previous)
    db.commit()
    return serialized(referral)


@router.get('/proyectos/{key}/ruta-emprendedora/notificaciones')
def route_notifications(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    staff = _is_staff(db, user, key)
    now = today()
    tomorrow = now + timedelta(days=1)
    tasks_query = select(TareaRutaEmprendedora).where(TareaRutaEmprendedora.proyecto_id == key, TareaRutaEmprendedora.estado.notin_(['Completada', 'Cancelada']))
    if not staff:
        tasks_query = tasks_query.where(TareaRutaEmprendedora.responsable_id == user.id)
    tasks = db.scalars(tasks_query.order_by(TareaRutaEmprendedora.fecha_objetivo)).all()
    notifications = []
    folder = db.get(ExpedienteIncubadora, project.id)
    if folder and folder.proxima_revision and folder.proxima_revision <= tomorrow and (staff or project.usuario_id == user.id):
        notifications.append({'tipo': 'revision', 'fecha': folder.proxima_revision.isoformat(), 'mensaje': f'Revisión próxima del proyecto {project.nombre}.'})
    settings = db.get(ConfiguracionIncubadora, 1)
    if staff and folder and settings and settings.dias_inactividad and folder.ultimo_movimiento <= now - timedelta(days=settings.dias_inactividad):
        notifications.append({'tipo': 'inactividad', 'fecha': folder.ultimo_movimiento.isoformat(), 'mensaje': f'El proyecto {project.nombre} no registra actividad desde hace {settings.dias_inactividad} días.'})
    for task in tasks:
        if not staff and task.creado_por != user.id and task.estado not in ('Completada', 'Cancelada'):
            notifications.append({'tipo': 'asignada', 'fecha': task.creado_en.date().isoformat(), 'mensaje': f'Tarea asignada: {task.nombre}. Fecha objetivo {task.fecha_objetivo}; evidencia esperada: {task.evidencia_esperada}.', 'tarea_id': str(task.id)})
        if not staff and task.estado_evidencia == 'Corrección requerida':
            notifications.append({'tipo': 'correccion', 'fecha': task.creado_en.date().isoformat(), 'mensaje': f'Se requiere corregir la evidencia de: {task.nombre}. {task.revision_notas}', 'tarea_id': str(task.id)})
        if task.estado_evidencia == 'Pendiente de revisión' and staff:
            notifications.append({'tipo': 'evidencia', 'fecha': now.isoformat(), 'mensaje': f'Evidencia pendiente de revisar: {task.nombre}', 'tarea_id': str(task.id)})
        if task.fecha_objetivo < now:
            notifications.append({'tipo': 'vencida', 'fecha': task.fecha_objetivo.isoformat(), 'mensaje': f'Tarea atrasada: {task.nombre}', 'tarea_id': str(task.id)})
        elif task.fecha_objetivo <= tomorrow:
            notifications.append({'tipo': 'proxima', 'fecha': task.fecha_objetivo.isoformat(), 'mensaje': f'Revisión próxima: {task.nombre}', 'tarea_id': str(task.id)})
    referrals = db.scalars(select(CanalizacionRutaEmprendedora).where(CanalizacionRutaEmprendedora.proyecto_id == key, CanalizacionRutaEmprendedora.estado == 'Abierta')).all()
    notifications.extend({'tipo': 'canalizacion', 'fecha': referral.fecha_objetivo.isoformat(), 'mensaje': f'Canalización abierta: {referral.destino}. Registra el resultado y evidencia de regreso.', 'canalizacion_id': str(referral.id)} for referral in referrals if staff or referral.creado_por == user.id or project.usuario_id == user.id)
    return {'items': notifications}


@router.get('/ruta-emprendedora/dashboard')
def route_dashboard(tipo_proyecto: Literal['normal', 'tecnologica', 'no_seguro'] | None = None, etapa: str | None = None, estado: str | None = None, asesor_id: UUID | None = None, desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    from app.modules.compartido.services import require_admin
    require_admin(user)
    if desde and hasta and desde > hasta:
        fail('La fecha inicial no puede ser posterior a la final.', 422)
    projects = {p.id: p for p in db.scalars(select(Proyecto)).all()}
    routes = {r.proyecto_id: r for r in db.scalars(select(RutaEmprendedora)).all()}
    folders = {f.proyecto_id: f for f in db.scalars(select(ExpedienteIncubadora)).all()}
    tasks = db.scalars(select(TareaRutaEmprendedora).order_by(TareaRutaEmprendedora.fecha_objetivo)).all()
    referrals = db.scalars(select(CanalizacionRutaEmprendedora).where(CanalizacionRutaEmprendedora.estado == 'Abierta').order_by(CanalizacionRutaEmprendedora.fecha_objetivo)).all()
    settings = db.get(ConfiguracionIncubadora, 1)
    inactivity_days = settings.dias_inactividad if settings else None
    items = []
    for project_id, project in projects.items():
        route = routes.get(project_id)
        if not route:
            continue
        project_day = project.creado_en.date() if project.creado_en else None
        folder = folders.get(project_id)
        route_type = route.tipo_proyecto or route.tipo_propuesto
        route_stage = (route.datos or {}).get('etapa_inicial')
        if tipo_proyecto and route_type != tipo_proyecto or etapa and route_stage != etapa or estado and route.estado != estado or asesor_id and (not folder or folder.asesor_id != asesor_id) or desde and (not project_day or project_day < desde) or hasta and (not project_day or project_day > hasta):
            continue
        project_tasks = [task for task in tasks if task.proyecto_id == project_id]
        pending_review = sum(task.estado_evidencia == 'Pendiente de revisión' for task in project_tasks)
        overdue = sum(task.fecha_objetivo < today() and task.estado not in ('Completada', 'Cancelada') for task in project_tasks)
        items.append({
            'proyecto_id': str(project_id), 'nombre': project.nombre, 'tipo_proyecto': route_type,
            'clasificacion_confirmada': route.clasificacion_confirmada, 'estado': route.estado,
            'tareas_atrasadas': overdue, 'evidencias_pendientes': pending_review,
            'canalizaciones_abiertas': sum(ref.proyecto_id == project_id for ref in referrals),
            'pasos_completados': sum(step.get('estado') in ('completado', 'no_aplica') for step in (route.pasos or {}).values()),
            'actualizado_en': route.actualizado_en.isoformat() if route.actualizado_en else None,
            'etapa_inicial': route_stage, 'asesor_id': str(folder.asesor_id) if folder and folder.asesor_id else None,
            'proxima_revision': folder.proxima_revision.isoformat() if folder and folder.proxima_revision else None,
            'sin_actividad': bool(inactivity_days and folder and folder.ultimo_movimiento <= today() - timedelta(days=inactivity_days)),
        })
    items.sort(key=lambda row: (row['estado'] == 'Concluido', row['nombre'].casefold()))
    included = {UUID(item['proyecto_id']) for item in items}
    upcoming = [task for task in tasks if task.proyecto_id in included and today() <= task.fecha_objetivo <= today() + timedelta(days=7) and task.estado not in ('Completada', 'Cancelada')]
    return {
        'proyectos': items,
        'tareas_atrasadas': [serialized(task) | {'proyecto_nombre': projects[task.proyecto_id].nombre} for task in tasks if task.proyecto_id in included and task.fecha_objetivo < today() and task.estado not in ('Completada', 'Cancelada')],
        'proximas_revisiones': [serialized(task) | {'proyecto_nombre': projects[task.proyecto_id].nombre} for task in upcoming],
        'evidencias_pendientes': [serialized(task) | {'proyecto_nombre': projects[task.proyecto_id].nombre} for task in tasks if task.proyecto_id in included and task.estado_evidencia == 'Pendiente de revisión'],
        'canalizaciones_abiertas': [serialized(referral) | {'proyecto_nombre': projects[referral.proyecto_id].nombre} for referral in referrals if referral.proyecto_id in included],
        'sin_actividad': [item for item in items if item['sin_actividad']],
    }


@router.get('/ruta-emprendedora/indicadores')
def route_indicators(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    from app.modules.compartido.services import require_admin
    require_admin(user)
    routes = db.scalars(select(RutaEmprendedora)).all()
    calculations = db.scalars(select(CalculoEconomico)).all()
    tasks = db.scalars(select(TareaRutaEmprendedora)).all()
    referrals = db.scalars(select(CanalizacionRutaEmprendedora)).all()
    counts = lambda values, get: {label: sum(get(row) == label for row in values) for label in sorted({get(row) for row in values if get(row)})}
    latest_calc = {}
    for calculation in calculations:
        if calculation.proyecto_id not in latest_calc or latest_calc[calculation.proyecto_id].version < calculation.version:
            latest_calc[calculation.proyecto_id] = calculation
    done = sum(task.estado == 'Completada' for task in tasks)
    return {
        'proyectos': len(routes),
        'tipos': counts(routes, lambda row: row.tipo_proyecto or row.tipo_propuesto),
        'estados': counts(routes, lambda row: row.estado),
        'semaforos_actuales': counts(latest_calc.values(), lambda row: row.semaforo),
        'tareas_completadas': done,
        'tareas_total': len(tasks),
        'porcentaje_tareas_completadas': round(done * 100 / len(tasks), 1) if tasks else 0,
        'canalizaciones_abiertas': sum(row.estado == 'Abierta' for row in referrals),
        'canalizaciones_cerradas': sum(row.estado == 'Cerrada' for row in referrals),
        'proyectos_con_pendiente_tecnico': sum(any(code == 'T3' and step.get('estado') not in ('completado', 'no_aplica') for code, step in (route.pasos or {}).items()) for route in routes),
        'nota': 'Cifras derivadas de expedientes reales; la evaluación económica es preliminar y orientativa.',
    }


@router.get('/proyectos/{key}/ruta-emprendedora/resumen.pdf')
def route_summary_pdf(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = _project_access(db, user, key)
    route = db.get(RutaEmprendedora, project.id)
    view = _route_view(db, project, route)
    from app.modules.incubadora.registration_pdf import build_route_summary_pdf
    return Response(build_route_summary_pdf(project, view), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="resumen-ruta-emprendedora.pdf"', 'Cache-Control': 'no-store'})
