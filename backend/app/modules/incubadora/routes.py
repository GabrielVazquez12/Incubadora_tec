"""Additive dossier endpoints; existing registration/admission remains authoritative."""
from datetime import date, timedelta, datetime, timezone
from typing import Literal
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from collections import Counter
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth.security import get_current_user
from app.models import Usuario, RolUsuario, Proyecto, HistorialEstatus, RegistroInicial, EquipoInnovaTec, Avance, Tarea, Documento, ConfiguracionIncubadora, ServicioCatalogo, HitoCatalogo, DiagnosticoIncubadora, ExpedienteIncubadora, AtencionIncubadora, ProyectoHito, CanalizacionIncubadora
from app.schemas.incubadora import ConfiguracionInput, ServicioInput, HitoInput, DiagnosticoInput, RegistroProyectoInput, AtencionInput, EstadoInput, AsignacionInput, CumplimientoInput, CanalizacionInput
from app.modules.compartido.services import admin, require_admin, fail, record, serialized, project_access, today
from app.modules.innovacion.services import audit, check_version
from app.modules.incubadora.services import next_review, inactive, expediente, diagnostic_for, evidence, responsible, diagnostic_view, last_movement, STATES
from app.modules.incubadora.registration_pdf import build_diagnostic_pdf

router = APIRouter(prefix='/portal/incubadora', tags=['Incubadora institucional'])
public = APIRouter(prefix='/public/incubadora', tags=['Incubadora pública'])


@public.get('/configuracion')
def public_config(db: Session = Depends(get_db)):
    row = db.get(ConfiguracionIncubadora, 1)
    return {'aviso_privacidad': row.aviso_privacidad if row and row.aviso_aprobado else '[Por definir: aviso de privacidad institucional aprobado]', 'aviso_aprobado': bool(row and row.aviso_aprobado), 'version': row.version if row else 0}


@router.get('/configuracion')
def config(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = db.get(ConfiguracionIncubadora, 1)
    return serialized(row) if row else {'version': 0, 'dias_inactividad': None, 'aviso_privacidad': '', 'aviso_aprobado': False}


@router.put('/configuracion')
def save_config(payload: ConfiguracionInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    # User lock serializes creation of singleton; unique PK protects concurrent coordinators.
    record(db, Usuario, user.id, lock=True)
    row = db.scalar(select(ConfiguracionIncubadora).where(ConfiguracionIncubadora.id == 1).with_for_update())
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('La configuración no existe.', 404)
    else:
        row = ConfiguracionIncubadora(id=1, version=0, historial=[])
        db.add(row)
    previous = {key: getattr(row, key) for key in ('dias_inactividad', 'aviso_aprobado', 'aviso_privacidad')}
    for key, value in payload.model_dump(exclude={'version'}).items():
        setattr(row, key, value)
    audit(row, user, 'configuracion', anterior=previous)
    db.commit()
    return serialized(row)


def catalogue(db, private=False):
    query = select(ServicioCatalogo).order_by(ServicioCatalogo.etapa, ServicioCatalogo.orden, ServicioCatalogo.nombre)
    if not private:
        query = query.where(ServicioCatalogo.activo)
    services = db.scalars(query).all()
    hitos = db.scalars(select(HitoCatalogo).where(HitoCatalogo.servicio_id.in_([s.id for s in services])).order_by(HitoCatalogo.orden, HitoCatalogo.nombre)).all()
    return {'servicios': [serialized(s) if private else {k: v for k, v in serialized(s).items() if k != 'historial'} for s in services], 'hitos': [serialized(h) if private else {k: v for k, v in serialized(h).items() if k != 'historial'} for h in hitos if private or h.activo]}


@public.get('/catalogo')
def public_catalogue(db: Session = Depends(get_db)):
    return catalogue(db)


@router.get('/catalogo')
def private_catalogue(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    return catalogue(db, True)


@router.post('/catalogo/propuesta')
def propose_catalogue(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    record(db, Usuario, user.id, lock=True)
    stages = (('Registro y diagnóstico', 'Idea y modelo de negocio', 'Proyecto académico o digital'), ('Cliente y mercado', 'Pruebas de validación', 'Costos y precios'), ('Ventas y comercialización', 'Marketing', 'Finanzas básicas'), ('SAT, legal y marca', 'Financiamiento', 'Bitácora y seguimiento'))
    for stage, names in enumerate(stages, 1):
        for order, name in enumerate(names):
            service_id = uuid5(NAMESPACE_URL, f'enlaces-its:catalogo:{stage}:{order}')
            service = db.get(ServicioCatalogo, service_id)
            if service is None:
                level = 2 if stage == 4 and order < 2 else 1
                service = ServicioCatalogo(id=service_id, nombre=name, etapa=stage, nivel=level, objetivo='[Por definir]', resultado_esperado='[Por definir]', canalizacion='[Por definir]' if level == 2 else '', orden=order, activo=True, version=0, historial=[])
                audit(service, user, 'propuesta_catalogo', origen='Texto proporcionado; nivel inicial sujeto a validación institucional')
                db.add(service)
                db.flush()
            milestone_id = uuid5(NAMESPACE_URL, f'enlaces-its:hito:{stage}:{order}')
            if db.get(HitoCatalogo, milestone_id) is None:
                milestone = HitoCatalogo(id=milestone_id, servicio_id=service_id, nombre=f'Completar: {name}', orden=order, activo=True, propuesta=True, version=0, historial=[])
                audit(milestone, user, 'propuesta_hito', aviso='Propuesta sujeta a validación de la Incubadora')
                db.add(milestone)
    db.commit()
    return catalogue(db, True)


def catalogue_save(db, user, key, payload, model):
    require_admin(user)
    row = db.scalar(select(model).where(model.id == key).with_for_update())
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('El elemento del catálogo no existe.', 404)
    else:
        row = model(id=key, version=0, historial=[])
        db.add(row)
    previous = serialized(row) if row.version else None
    if previous:
        previous.pop('historial', None)
    for name, value in payload.model_dump(exclude={'version'}).items():
        setattr(row, name, value)
    audit(row, user, 'catalogo', anterior=previous)
    db.commit()
    return serialized(row)


@router.put('/catalogo/{key}')
def save_service(key: UUID, payload: ServicioInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return catalogue_save(db, user, key, payload, ServicioCatalogo)


@router.put('/hitos/{key}')
def save_hito(key: UUID, payload: HitoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    record(db, ServicioCatalogo, payload.servicio_id)
    return catalogue_save(db, user, key, payload, HitoCatalogo)


@router.put('/diagnosticos/{key}')
def save_diagnostic(key: UUID, payload: DiagnosticoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = project_access(db, user, payload.proyecto_id, owner_only=True) if payload.proyecto_id else None
    source = record(db, RegistroInicial, payload.registro_id, lock=True) if payload.registro_id else None
    owner_id = project.usuario_id if project else source.user
    if owner_id != user.id:
        fail('El diagnóstico y consentimiento los confirma el titular.', 403)
    if source and (source.user != owner_id or project and project.registro_id != source.id):
        fail('El registro debe ser el origen del proyecto.', 422)
    # Owner lock also serializes creation for the same origin.
    record(db, Usuario, owner_id, lock=True)
    row = db.scalar(select(DiagnosticoIncubadora).where(DiagnosticoIncubadora.id == key).with_for_update())
    config_row = db.get(ConfiguracionIncubadora, 1)
    if not config_row or not config_row.aviso_aprobado:
        fail('El diagnóstico estará disponible cuando se publique el aviso aprobado.', 409)
    if payload.version_aviso != config_row.version:
        fail('El aviso cambió. Revísalo y confirma nuevamente.', 409)
    if row:
        if row.usuario_id != owner_id or row.proyecto_id != payload.proyecto_id or row.registro_id != payload.registro_id:
            fail('Conserva el origen del diagnóstico.', 409)
        check_version(row, payload.version)
    elif payload.version:
        fail('El diagnóstico no existe.', 404)
    else:
        filters = []
        if payload.proyecto_id:
            filters.append(DiagnosticoIncubadora.proyecto_id == payload.proyecto_id)
        if payload.registro_id:
            filters.append(DiagnosticoIncubadora.registro_id == payload.registro_id)
        if db.scalar(select(DiagnosticoIncubadora.id).where(or_(*filters))):
            fail('El origen ya tiene un diagnóstico; edítalo sin duplicarlo.', 409)
        row = DiagnosticoIncubadora(id=key, usuario_id=owner_id, proyecto_id=payload.proyecto_id, registro_id=payload.registro_id, version=0, historial=[])
        db.add(row)
    previous = row.datos
    row.datos = payload.model_dump(mode='json', exclude={'version', 'proyecto_id', 'registro_id', 'acepto_privacidad', 'version_aviso'})
    row.consentimiento = {'texto': config_row.aviso_privacidad, 'version': config_row.version, 'fecha': datetime.now(timezone.utc).isoformat(), 'usuario_id': str(user.id)}
    audit(row, user, 'diagnostico', anterior=previous)
    if project:
        folder = expediente(db, project, user, True)
        folder.ultimo_movimiento = today()
        if folder.proxima_revision is None:
            folder.proxima_revision = next_review(today(), payload.frecuencia)
        audit(folder, user, 'diagnostico', diagnostico_id=str(row.id))
    db.commit()
    return diagnostic_view(row)


@router.post('/registro/{key}', status_code=201)
def register_project(key: UUID, payload: RegistroProyectoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if user.rol != RolUsuario.estudiante:
        fail('Confirma el registro desde una cuenta de emprendedor. Las cuentas externas conservan Solicitud de ingreso.', 403)
    record(db, Usuario, user.id, lock=True)
    project = db.get(Proyecto, key)
    diagnosis_id = uuid5(NAMESPACE_URL, f'enlaces-its:diagnostico:{key}')
    body = payload.model_dump(exclude={'nombre', 'producto_servicio'})
    body['proyecto_id'] = key
    data = DiagnosticoInput.model_validate(body)
    if project:
        if project.usuario_id != user.id:
            fail('No tienes acceso a este registro.', 403)
        existing = db.get(DiagnosticoIncubadora, diagnosis_id)
        expected = data.model_dump(mode='json', exclude={'version', 'proyecto_id', 'registro_id', 'acepto_privacidad', 'version_aviso'})
        if existing and existing.datos == expected and project.nombre == payload.nombre and project.producto_servicio == payload.producto_servicio:
            return diagnostic_view(existing)
        fail('El registro ya existe. Continúa desde su expediente sin duplicarlo.', 409)
    project = Proyecto(id=key, usuario_id=user.id, nombre=payload.nombre, descripcion=payload.descripcion, producto_servicio=payload.producto_servicio, telefono=payload.telefono, especialidad=payload.carrera, estatus='En revisión', progreso=0, siguiente_paso='Diagnóstico y primer contacto')
    db.add(project)
    db.flush()
    db.add(HistorialEstatus(proyecto_id=key, cambiado_por_id=user.id, estatus_nuevo='En revisión', comentario='Registro y diagnóstico inicial de Enlaces Institucionales ITS'))
    return save_diagnostic(diagnosis_id, data, db, user)


@router.get('/registros/{key}/diagnostico')
def registration_diagnostic(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    source = record(db, RegistroInicial, key)
    if not admin(user) and source.user != user.id:
        fail('No tienes acceso a este registro.', 403)
    row = db.scalar(select(DiagnosticoIncubadora).where(DiagnosticoIncubadora.registro_id == key))
    return diagnostic_view(row)


@router.get('/diagnosticos/{key}/registro.pdf')
def diagnostic_pdf(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    row = record(db, DiagnosticoIncubadora, key)
    if not admin(user) and row.usuario_id != user.id:
        fail('No tienes acceso al diagnóstico.', 403)
    owner = record(db, Usuario, row.usuario_id)
    name = record(db, Proyecto, row.proyecto_id).nombre if row.proyecto_id else record(db, RegistroInicial, row.registro_id).datos.get('empresa.nombre', 'Registro de ingreso')
    return Response(build_diagnostic_pdf(row, owner, name), media_type='application/pdf', headers={'Content-Disposition': 'attachment; filename="registro-diagnostico.pdf"', 'Cache-Control': 'no-store'})


@router.get('/proyectos/{key}')
def dossier(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = project_access(db, user, key)
    folder = expediente(db, project, user)
    diagnosis = diagnostic_for(db, project)
    owner = record(db, Usuario, project.usuario_id)
    advances = db.scalars(select(Avance).where(Avance.project == key)).all()
    attention = db.scalars(select(AtencionIncubadora).where(AtencionIncubadora.proyecto_id == key).order_by(AtencionIncubadora.fecha.desc(), AtencionIncubadora.creado_en.desc())).all()
    milestones = db.scalars(select(ProyectoHito).where(ProyectoHito.proyecto_id == key)).all()
    referrals = db.scalars(select(CanalizacionIncubadora).where(CanalizacionIncubadora.proyecto_id == key)).all()
    team = db.scalar(select(EquipoInnovaTec).where(EquipoInnovaTec.proyecto_id == key))
    return {'proyecto': serialized(project), 'titular': {'id': str(owner.id), 'nombre': owner.nombre, 'correo': owner.correo}, 'expediente': serialized(folder) if folder else {'version': 0, 'estado': 'activo', 'proxima_revision': None, 'historial': []}, 'diagnostico': diagnostic_view(diagnosis), 'atenciones': [serialized(a) for a in attention], 'avances': [serialized(a) for a in advances], 'hitos': [serialized(h) for h in milestones], 'canalizaciones': [serialized(c) for c in referrals], 'equipo_innovatec_id': str(team.id) if team else None, 'catalogo': catalogue(db), 'transiciones': list(STATES[folder.estado if folder else 'activo'])}


@router.post('/proyectos/{key}/atenciones/{attention_id}')
def save_attention(key: UUID, attention_id: UUID, payload: AtencionInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    project = project_access(db, user, key)
    folder = expediente(db, project, user, True)
    previous = db.get(AtencionIncubadora, attention_id)
    if previous:
        if previous.proyecto_id != key:
            fail('No se puede mover una atención a otro proyecto.', 409)
        same = all(getattr(previous, field) == value for field, value in payload.model_dump(exclude={'version'}).items())
        if not same:
            fail('La atención está registrada. Crea otra para conservar la bitácora.', 409)
        return serialized(previous)
    check_version(folder, payload.version)
    if payload.fecha > today():
        fail('La fecha de una atención realizada no puede ser futura.', 422)
    if folder.estado in ('concluido', 'formalizado'):
        fail('Reabre el proyecto antes de registrar una atención.', 409)
    if folder.estado == 'pausado' and payload.tipo != 'recuperacion':
        fail('Registra una atención de recuperación para reactivar el proyecto.', 409)
    if payload.tipo == 'recuperacion' and folder.estado != 'pausado':
        # Inactive active projects may receive recovery without changing status twice.
        settings = db.get(ConfiguracionIncubadora, 1)
        if not inactive(folder, settings.dias_inactividad if settings else None, today()):
            fail('La recuperación corresponde a proyectos pausados o inactivos.', 409)
    responsible(db, project, payload.responsable_id)
    evidence(db, key, payload)
    if payload.servicio_id and not record(db, ServicioCatalogo, payload.servicio_id).activo:
        fail('Selecciona un servicio activo.', 422)
    row = AtencionIncubadora(id=attention_id, proyecto_id=key, registrado_por=user.id, **payload.model_dump(exclude={'version'}))
    db.add(row)
    if payload.tipo == 'recuperacion':
        folder.estado, folder.motivo, folder.fecha_estado = 'activo', '', today()
    folder.proxima_revision, folder.ultimo_movimiento = payload.fecha_revision, today()
    if folder.estado == 'activo' and payload.tipo != 'recuperacion':
        folder.estado = 'en_seguimiento'
    audit(folder, user, 'atencion', atencion_id=str(attention_id), tipo=payload.tipo)
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/estado')
def save_status(key: UUID, payload: EstadoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    project = project_access(db, user, key)
    row = expediente(db, project, user, True)
    check_version(row, payload.version)
    if payload.estado not in STATES[row.estado] or row.estado == 'pausado' and payload.estado == 'activo':
        fail('Usa una transición válida; la pausa se reactiva con una atención de recuperación.', 409)
    if payload.fecha > today():
        fail('La fecha de cambio de estado no puede ser futura.', 422)
    if payload.estado in ('pausado', 'concluido', 'formalizado'):
        last = db.scalar(select(AtencionIncubadora.id).where(AtencionIncubadora.proyecto_id == key, AtencionIncubadora.tipo == 'cierre', AtencionIncubadora.fecha == payload.fecha).limit(1))
        if not last:
            fail('Registra primero una atención de cierre con actividad, responsable y revisión.', 409)
    previous = row.estado
    row.estado, row.motivo, row.fecha_estado, row.ultimo_movimiento = payload.estado, payload.motivo, payload.fecha, today()
    audit(row, user, 'estado', anterior=previous, estado=payload.estado, motivo=payload.motivo)
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/asesor')
def assign(key: UUID, payload: AsignacionInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    project = project_access(db, user, key)
    advisor = record(db, Usuario, payload.asesor_id)
    if not admin(advisor):
        fail('Selecciona un usuario con permisos de coordinación.', 422)
    if payload.primer_contacto > today():
        fail('La fecha del primer contacto no puede ser futura.', 422)
    row = expediente(db, project, user, True)
    check_version(row, payload.version)
    row.asesor_id, row.primer_contacto = advisor.id, payload.primer_contacto
    audit(row, user, 'asignacion', asesor_id=str(advisor.id))
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/hitos/{hito_id}')
def save_progress(key: UUID, hito_id: UUID, payload: CumplimientoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = project_access(db, user, key)
    hito = record(db, HitoCatalogo, hito_id)
    if not hito.activo or not record(db, ServicioCatalogo, hito.servicio_id).activo:
        fail('Selecciona un hito activo.', 422)
    row = db.get(ProyectoHito, (key, hito_id))
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('El hito aún no está registrado en el proyecto.', 409)
    else:
        row = ProyectoHito(proyecto_id=key, hito_id=hito_id, version=0, historial=[])
        db.add(row)
    folder = expediente(db, project, user, True)
    if folder.estado in ('pausado', 'concluido', 'formalizado'):
        fail('Coordina la reactivación antes de registrar un hito.', 409)
    if payload.fecha and payload.fecha > today():
        fail('La fecha del hito realizado no puede ser futura.', 422)
    evidence(db, key, payload)
    before = row.estado
    for field, value in payload.model_dump(exclude={'version'}).items():
        setattr(row, field, value)
    audit(row, user, 'hito', anterior=before, estado=row.estado)
    folder.ultimo_movimiento = today()
    audit(folder, user, 'hito', hito_id=str(hito_id), estado=row.estado)
    db.commit()
    return serialized(row)


@router.put('/proyectos/{key}/canalizaciones/{referral_id}')
def save_referral(key: UUID, referral_id: UUID, payload: CanalizacionInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    project_access(db, user, key)
    attention = record(db, AtencionIncubadora, payload.atencion_id)
    if attention.proyecto_id != key or attention.tipo != 'canalizacion':
        fail('Enlaza una atención de canalización del mismo proyecto.', 422)
    if payload.fecha > today():
        fail('La fecha de canalización realizada no puede ser futura.', 422)
    evidence(db, key, payload)
    row = db.scalar(select(CanalizacionIncubadora).where(CanalizacionIncubadora.id == referral_id).with_for_update())
    if row:
        if row.proyecto_id != key or row.atencion_id != payload.atencion_id:
            fail('Conserva el origen de la canalización.', 409)
        check_version(row, payload.version)
    elif payload.version:
        fail('La canalización no existe.', 404)
    else:
        row = CanalizacionIncubadora(id=referral_id, proyecto_id=key, version=0, historial=[])
        db.add(row)
    for field, value in payload.model_dump(exclude={'version'}).items():
        setattr(row, field, value)
    audit(row, user, 'canalizacion', resultado=payload.resultado)
    db.commit()
    return serialized(row)


@router.get('/seguimientos')
def followups(vista: Literal['semana', 'vencidos', 'inactivos'] = 'semana', db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    settings = db.get(ConfiguracionIncubadora, 1)
    threshold = settings.dias_inactividad if settings else None
    day = today()
    first = day - timedelta(days=day.weekday())
    rows = db.execute(select(ExpedienteIncubadora, Proyecto).join(Proyecto, Proyecto.id == ExpedienteIncubadora.proyecto_id)).all()
    selected = []
    for row, project in rows:
        matches = inactive(row, threshold, day) if vista == 'inactivos' else row.estado in ('activo', 'en_seguimiento') and row.proxima_revision is not None and (row.proxima_revision < day if vista == 'vencidos' else first <= row.proxima_revision <= first + timedelta(days=6))
        if matches:
            selected.append({**serialized(row), 'nombre': project.nombre})
    if vista == 'inactivos' and threshold is not None:
        known = {project.id for _, project in rows}
        for project in db.scalars(select(Proyecto).where(Proyecto.estatus != 'Completado')):
            if project.id not in known:
                last = last_movement(db, project)
                if (day - last).days >= threshold:
                    selected.append({'id': str(project.id), 'proyecto_id': str(project.id), 'nombre': project.nombre, 'estado': 'activo', 'proxima_revision': None, 'ultimo_movimiento': last.isoformat(), 'motivo': '', 'version': 0})
    selected.sort(key=lambda row: (row['proxima_revision'] or '9999-12-31', row['nombre']))
    return {'items': selected, 'dias_inactividad': threshold, 'criterio_configurado': threshold is not None}


@router.get('/indicadores')
def indicators(desde: date | None = None, hasta: date | None = None, perfil: str | None = None, etapa: str | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    if desde and hasta and desde > hasta:
        fail('La fecha inicial no puede ser posterior a la final.', 422)
    query = select(Proyecto)
    if desde:
        query = query.where(Proyecto.creado_en >= datetime.combine(desde, datetime.min.time()))
    if hasta:
        query = query.where(Proyecto.creado_en < datetime.combine(hasta + timedelta(days=1), datetime.min.time()))
    projects = db.scalars(query).all()
    pairs = [(p, diagnostic_for(db, p)) for p in projects]
    pairs = [(p, d) for p, d in pairs if (not perfil or d and d.datos.get('perfil') == perfil) and (not etapa or d and d.datos.get('etapa') == etapa)]
    pids = [p.id for p, _ in pairs]
    rows = db.scalars(select(ExpedienteIncubadora).where(ExpedienteIncubadora.proyecto_id.in_(pids))).all()
    distribution = {field: dict(Counter(d.datos.get(field) for _, d in pairs if d and d.datos.get(field))) for field in ('perfil', 'etapa', 'canal_llegada', 'frecuencia', 'modalidad')}
    distribution['necesidades'] = dict(Counter(n for _, d in pairs if d for n in d.datos.get('necesidades', [])))
    counts = Counter(row.estado for row in rows)
    counts['activo'] += len(pids) - len(rows)
    completed_tasks = db.scalar(select(func.count()).select_from(Tarea).where(Tarea.project.in_(pids), Tarea.estatus == 'Completado'))
    completed_hitos = db.scalar(select(func.count()).select_from(ProyectoHito).where(ProyectoHito.proyecto_id.in_(pids), ProyectoHito.estado == 'cumplido'))
    return {'proyectos': len(pids), 'usuarios': len({p.usuario_id for p, _ in pairs}), 'diagnosticos': sum(d is not None for _, d in pairs), 'estados': dict(counts), 'actividades_completadas': completed_tasks + completed_hitos, 'formalizados': counts['formalizado'], 'concluidos': counts['concluido'], 'vendiendo_o_formalizados': sum(d is not None and d.datos.get('etapa') == 'vendiendo o formalizado' for _, d in pairs), 'seguimientos_vencidos': sum(row.estado in ('activo', 'en_seguimiento') and row.proxima_revision is not None and row.proxima_revision < today() for row in rows), 'distribucion': distribution, 'periodo_sobre': 'Fecha de creación del proyecto; los estados y avances muestran la situación actual.'}
