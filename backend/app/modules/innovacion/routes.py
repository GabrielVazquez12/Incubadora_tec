"""Local InnovaTec endpoints, additive to the existing proposal workflow."""
from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import select, func
from sqlalchemy.orm import Session, defer
from app.auth.security import get_current_user
from app.database import get_db
from app.document_storage import store_bytes, read_bytes
from app.document_validation import MAX_DOCUMENT_BYTES, validate_document
from app.models import Usuario, RolUsuario, Innovacion, Proyecto, HistorialEstatus, Evento, Inscripcion, PlaticaInnovaTec, ConvocatoriaInnovaTec, ArchivoConvocatoriaInnovaTec, EquipoInnovaTec, IntegranteInnovaTec, DocumentoInnovaTec
from app.modules.compartido.documents import download_response
from app.modules.compartido.event_certificates import build_innovatec_diploma
from app.schemas.validation import valid_text
from app.modules.compartido.services import admin, require_admin, record, fail, serialized, today
from app.modules.compartido.mutations import save_innovation, INNOVATION_CATALOG
from app.modules.coordinacion.mutations import save_events
from app.schemas.portal import InnovationInput
from app.schemas.innovatec import ConvocatoriaInput, EquipoInput, EquipoEditInput, CambioEstado, RevisionDocumento, SeguimientoInput, DiplomaInput, PlaticaInput
from app.modules.innovacion.services import audit, check_version, team_access, team_view, convocatoria_view, transition, file_metadata

router = APIRouter(prefix="/portal/innovatec", tags=["InnovaTec local"])
public = APIRouter(prefix="/public/innovatec", tags=["InnovaTec público"])


def check_categories(values):
    allowed = {item[0] for item in INNOVATION_CATALOG['certamen']['items']}
    if any(value not in allowed for value in values):
        fail("Selecciona categorías del Certamen de Proyectos existente.", 422)


@public.get('/convocatorias')
def public_calls(db: Session = Depends(get_db)):
    return [convocatoria_view(db, row) for row in db.scalars(select(ConvocatoriaInnovaTec).where(ConvocatoriaInnovaTec.publicada).order_by(ConvocatoriaInnovaTec.anio.desc()))]


@router.get('/convocatorias')
def calls(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    return [convocatoria_view(db, row, True) for row in db.scalars(select(ConvocatoriaInnovaTec).order_by(ConvocatoriaInnovaTec.anio.desc()))]


@router.put('/convocatorias/{key}')
def save_call(key: UUID, payload: ConvocatoriaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    check_categories(payload.categorias)
    row = db.scalar(select(ConvocatoriaInnovaTec).where(ConvocatoriaInnovaTec.id == key).with_for_update())
    previous = {'anio': row.anio, 'datos': row.datos, 'publicada': row.publicada} if row else None
    if db.scalar(select(ConvocatoriaInnovaTec.id).where(ConvocatoriaInnovaTec.anio == payload.anio, ConvocatoriaInnovaTec.id != key)):
        fail("Ya existe una convocatoria para ese año.", 409)
    if row:
        check_version(row, payload.version)
        if row.anio != payload.anio and db.scalar(select(EquipoInnovaTec.id).where(EquipoInnovaTec.convocatoria_id == key).limit(1)):
            fail("Conserva el año de una convocatoria que ya tiene equipos inscritos.", 409)
    elif payload.version:
        fail("La convocatoria no existe.", 404)
    else:
        row = ConvocatoriaInnovaTec(id=key, version=0, historial=[])
        db.add(row)
    row.anio, row.publicada = payload.anio, payload.publicada
    row.datos = payload.model_dump(mode='json', exclude={'anio', 'publicada', 'version'})
    audit(row, user, 'convocatoria', publicada=row.publicada, anterior=previous)
    db.commit()
    return convocatoria_view(db, row, True)


def uploaded_file(db, file, namespace):
    try:
        content = file.file.read(MAX_DOCUMENT_BYTES + 1)
    finally:
        file.file.close()
    mime = validate_document(file.filename, content)
    stored = store_bytes(db, content, mime, namespace)
    return dict(nombre=file.filename, mime=mime, bucket=stored['bucket'], clave=stored['key'], contenido=stored['content'])


@router.post('/convocatorias/{key}/archivos', status_code=201)
def call_upload(key: UUID, file: UploadFile = File(...), tipo: Literal['convocatoria', 'manual', 'anexo'] = Form(...), version_manual: str = Form('', max_length=160), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    try:
        valid_text(version_manual)
    except ValueError:
        fail("La versión del manual contiene caracteres no válidos.", 422)
    row = record(db, ConvocatoriaInnovaTec, key, lock=True)
    if tipo == 'manual' and not version_manual.strip():
        fail("Indica la versión del manual.", 422)
    values = uploaded_file(db, file, f'innovatec/convocatorias/{key}')
    if tipo != 'anexo':
        for previous in db.scalars(select(ArchivoConvocatoriaInnovaTec).where(ArchivoConvocatoriaInnovaTec.convocatoria_id == key, ArchivoConvocatoriaInnovaTec.tipo == tipo, ArchivoConvocatoriaInnovaTec.vigente)):
            previous.vigente = False
    doc = ArchivoConvocatoriaInnovaTec(id=uuid4(), convocatoria_id=key, tipo=tipo, version_manual=version_manual.strip(), **values)
    db.add(doc)
    if tipo == 'manual':
        row.datos = {**row.datos, 'version_manual': version_manual.strip()}
    audit(row, user, 'archivo_convocatoria', archivo_id=str(doc.id), tipo=tipo, version_manual=version_manual.strip())
    db.commit()
    return file_metadata(doc)


@public.get('/archivos/{key}')
def public_file(key: UUID, db: Session = Depends(get_db)):
    doc = record(db, ArchivoConvocatoriaInnovaTec, key)
    call = record(db, ConvocatoriaInnovaTec, doc.convocatoria_id)
    if not call.publicada or not doc.vigente:
        fail("Archivo no publicado.", 404)
    return download_response(read_bytes(doc.bucket, doc.clave, doc.contenido), doc.mime, doc.nombre)


@router.get('/archivos/{key}')
def private_call_file(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    doc = record(db, ArchivoConvocatoriaInnovaTec, key)
    return download_response(read_bytes(doc.bucket, doc.clave, doc.contenido), doc.mime, doc.nombre)


def roster(db, team, members):
    existing = {m.correo: m for m in db.scalars(select(IntegranteInnovaTec).where(IntegranteInnovaTec.equipo_id == team.id))}
    desired = {m.correo for m in members}
    for email, item in existing.items():
        item.vigente = email in desired
    for member in members:
        item = existing.get(member.correo)
        if item is None:
            item = IntegranteInnovaTec(id=uuid4(), equipo_id=team.id, diploma_estado='pendiente', vigente=True)
            db.add(item)
        for key, value in member.model_dump().items():
            setattr(item, key, value)


@router.post('/equipos', status_code=201)
def register_team(payload: EquipoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if user.rol != RolUsuario.estudiante:
        fail("La inscripción la confirma la cuenta del emprendedor responsable.", 403)
    existing = db.get(EquipoInnovaTec, payload.id)
    if existing:
        team, source = team_access(db, user, payload.id, lock=False)
        return team_view(db, team, source, True)
    if payload.innovacion_id:
        candidate = record(db, Innovacion, payload.innovacion_id)
        if candidate.user != user.id:
            fail("La propuesta no pertenece a tu cuenta.", 403)
        already = db.scalar(select(EquipoInnovaTec).where(EquipoInnovaTec.innovacion_id == candidate.id))
        if already:
            return team_view(db, already, candidate, True)
    # Existing proposal writes lock the proposal before its owner; preserve that order.
    linked_source = record(db, Innovacion, payload.innovacion_id, lock=True) if payload.innovacion_id else None
    if linked_source:
        db.refresh(linked_source)
        already = db.scalar(select(EquipoInnovaTec).where(EquipoInnovaTec.innovacion_id == linked_source.id))
        if already:
            return team_view(db, already, linked_source, True)
    if linked_source and linked_source.user != user.id:
        fail("La propuesta no pertenece a tu cuenta.", 403)
    if not linked_source and db.get(Innovacion, payload.id):
        if db.get(EquipoInnovaTec, payload.id):
            team, source = team_access(db, user, payload.id, lock=False)
            return team_view(db, team, source, True)
        fail("Vincula la propuesta existente mediante su identificador.", 409)
    record(db, Usuario, user.id, lock=True)
    existing = db.get(EquipoInnovaTec, payload.id)
    if existing:
        team, source = team_access(db, user, payload.id)
        return team_view(db, team, source, True)  # Safe retry after a lost response.
    call = record(db, ConvocatoriaInnovaTec, payload.convocatoria_id, lock=True)
    check_version(call, payload.version_convocatoria)
    if not call.publicada or not call.datos.get('aviso_aprobado') or not call.datos['apertura'] <= today().isoformat() <= call.datos['cierre']:
        fail("La convocatoria no está abierta para inscripciones.", 409)
    if payload.categoria not in call.datos['categorias']:
        fail("La categoría no está disponible en esta convocatoria.", 422)
    participant = next(m for m in payload.integrantes if m.tipo == 'participante')
    advisor = next(m for m in payload.integrantes if m.tipo == 'asesor')
    if payload.innovacion_id:
        source = linked_source
        if source.user != user.id:
            fail("La propuesta no pertenece a tu cuenta.", 403)
        expected = {'nombre': payload.nombre, 'equipo': payload.equipo, 'descripcion': payload.descripcion, 'categoria': payload.categoria, 'modulo': INNOVATION_CATALOG['certamen']['title']}
        if any(source.datos.get(k) != v for k, v in expected.items()):
            fail("Conserva los datos de la propuesta vinculada; corrígela desde su módulo si es necesario.", 409)
    else:
        proposal = InnovationInput(nombre=payload.nombre, equipo=payload.equipo, lider=participant.nombre, asesor=advisor.nombre, descripcion=payload.descripcion, modulo=INNOVATION_CATALOG['certamen']['title'], categoria=payload.categoria, estatus='En revisión')
        _, values = save_innovation(db, user, payload.id, proposal.model_dump(), None, proposal.model_dump(), True, 'innovation')
        source = Innovacion(id=payload.id, **values)
        db.add(source)
    db.flush()
    team = EquipoInnovaTec(id=payload.id, innovacion_id=source.id, convocatoria_id=call.id, folio=f'ITS-INN-{call.anio}-{payload.id.hex}', estado='inscrito', version=0, historial=[], seguimiento={}, consentimiento={'version': call.version, 'fecha': datetime.now(timezone.utc).isoformat(), 'aviso': call.datos['aviso_privacidad'], 'requisitos': call.datos['requisitos']})
    db.add(team)
    audit(team, user, 'inscripcion', propuesta_id=str(source.id))
    db.flush()
    roster(db, team, payload.integrantes)
    db.commit()
    return team_view(db, team, source, True)


@router.get('/equipos')
def teams(anio: int | None = Query(None, ge=2000, le=2100), estado: Literal['inscrito','documentacion_recibida','etapa_local','acreditado','etapa_regional','etapa_nacional','no_acreditado','baja'] | None = None, etapa: Literal['Local', 'Regional', 'Nacional'] | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    query = select(EquipoInnovaTec).join(Innovacion, EquipoInnovaTec.innovacion_id == Innovacion.id).join(ConvocatoriaInnovaTec, EquipoInnovaTec.convocatoria_id == ConvocatoriaInnovaTec.id)
    if not admin(user):
        query = query.where(Innovacion.user == user.id)
    if anio:
        query = query.where(ConvocatoriaInnovaTec.anio == anio)
    if estado:
        query = query.where(EquipoInnovaTec.estado == estado)
    if etapa:
        query = query.where(Innovacion.datos['etapa'].as_string() == etapa)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.scalars(query.order_by(EquipoInnovaTec.creado_en.desc()).offset(offset).limit(limit)).all()
    return {'total': total, 'items': [team_view(db, t, db.get(Innovacion, t.innovacion_id)) for t in rows]}


@router.get('/equipos/{key}')
def team_detail(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    team, source = team_access(db, user, key, lock=False)
    return team_view(db, team, source, True)


@router.put('/equipos/{key}')
def edit_team(key: UUID, payload: EquipoEditInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    team, source = team_access(db, user, key)
    if source.user != user.id or admin(user):
        fail("Los datos de captura los modifica el responsable de la propuesta.", 403)
    check_version(team, payload.version)
    if key != payload.id or payload.convocatoria_id != team.convocatoria_id or payload.innovacion_id != source.id:
        fail("No cambies las relaciones del expediente.", 422)
    if payload.version_convocatoria != team.consentimiento['version']:
        fail("Conserva la versión de consentimiento aceptada al inscribirte.", 422)
    if team.estado not in ('inscrito', 'documentacion_recibida'):
        fail("Los datos de participación ya están cerrados.", 409)
    if db.scalar(select(IntegranteInnovaTec.id).where(IntegranteInnovaTec.equipo_id == key, IntegranteInnovaTec.diploma_estado != 'pendiente').limit(1)):
        fail("El equipo tiene diplomas registrados; coordina la corrección antes de cambiar integrantes.", 409)
    if payload.categoria != source.datos['categoria']:
        fail("Conserva la categoría de la propuesta.", 409)
    record(db, Usuario, user.id, lock=True)
    other = db.scalars(select(Innovacion).where(Innovacion.user == user.id, Innovacion.id != source.id))
    if any(p.datos.get('nombre', '').casefold() == payload.nombre.casefold() and p.datos.get('categoria') == payload.categoria and p.datos.get('modulo') == source.datos['modulo'] for p in other):
        fail("Ya existe una propuesta con ese nombre en esta categoría.", 409)
    previous_source = dict(source.datos)
    source.datos = {**source.datos, 'nombre': payload.nombre, 'equipo': payload.equipo, 'descripcion': payload.descripcion, 'lider': next(m.nombre for m in payload.integrantes if m.tipo == 'participante'), 'asesor': next(m.nombre for m in payload.integrantes if m.tipo == 'asesor')}
    old = [serialized(m) for m in db.scalars(select(IntegranteInnovaTec).where(IntegranteInnovaTec.equipo_id == key, IntegranteInnovaTec.vigente))]
    roster(db, team, payload.integrantes)
    source.datos = {**source.datos, 'estatus': 'En revisión', 'historial': [*source.datos.get('historial', []), {'fecha': datetime.now(timezone.utc).isoformat(), 'nombre': user.nombre, 'estatus': 'En revisión', 'etapa': source.datos['etapa'], 'observaciones': 'Captura de equipo actualizada; requiere revisión.'}]}
    audit(team, user, 'captura_editada', integrantes_anteriores=old, propuesta_anterior=previous_source)
    db.commit()
    return team_view(db, team, source, True)


@router.post('/equipos/{key}/estado')
def change_state(key: UUID, payload: CambioEstado, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    team, source = team_access(db, user, key)
    if not admin(user) and payload.estado != 'baja':
        require_admin(user)
    if payload.estado == 'etapa_local' and source.datos.get('estatus') != 'Aprobada':
        fail("Aprueba la propuesta existente antes de admitirla a la etapa local.", 422)
    transition(db, team, user, payload)
    next_stage = {'etapa_local': 'Local', 'etapa_regional': 'Regional', 'etapa_nacional': 'Nacional'}.get(team.estado)
    if next_stage and source.datos.get('etapa') != next_stage:
        trail = [*source.datos.get('historial', []), {'fecha': datetime.now(timezone.utc).isoformat(), 'nombre': user.nombre, 'estatus': source.datos['estatus'], 'etapa': next_stage, 'observaciones': payload.motivo}]
        source.datos = {**source.datos, 'etapa': next_stage, 'historial': trail}
    db.commit()
    return team_view(db, team, source, True)


@router.put('/equipos/{key}/seguimiento')
def logistics(key: UUID, payload: SeguimientoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    team, source = team_access(db, user, key)
    check_version(team, payload.version)
    team.seguimiento = {**team.seguimiento, payload.etapa: payload.model_dump(mode='json', exclude={'version'})}
    audit(team, user, 'seguimiento', etapa=payload.etapa)
    db.commit()
    return team_view(db, team, source, True)


@router.post('/equipos/{key}/documentos', status_code=201)
def upload_document(key: UUID, requisito: str = Form(..., max_length=160), file: UploadFile = File(...), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    team, source = team_access(db, user, key)
    if team.estado == 'baja' or requisito not in team.consentimiento['requisitos']:
        fail("El requisito no está disponible para este expediente.", 422)
    previous = db.scalar(select(DocumentoInnovaTec).where(DocumentoInnovaTec.equipo_id == key, DocumentoInnovaTec.requisito == requisito, DocumentoInnovaTec.vigente))
    if previous and previous.estado != 'observado':
        fail("Solo puedes reemplazar documentos con observaciones.", 409)
    values = uploaded_file(db, file, f'innovatec/equipos/{key}')
    if previous:
        previous.vigente = False
        db.flush()
    doc = DocumentoInnovaTec(id=uuid4(), equipo_id=key, requisito=requisito, estado='recibido', vigente=True, comentarios='', **values)
    db.add(doc)
    audit(team, user, 'documento', documento_id=str(doc.id), requisito=requisito, reemplaza=str(previous.id) if previous else None)
    db.commit()
    return team_view(db, team, source, True)


@router.get('/documentos/{key}')
def download_document(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    doc = record(db, DocumentoInnovaTec, key)
    team_access(db, user, doc.equipo_id, lock=False)
    return download_response(read_bytes(doc.bucket, doc.clave, doc.contenido), doc.mime, doc.nombre)


@router.post('/documentos/{key}/revision')
def review_document(key: UUID, payload: RevisionDocumento, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    # Acquire team lock before document lock, matching upload lock ordering.
    doc = record(db, DocumentoInnovaTec, key)
    team, source = team_access(db, user, doc.equipo_id)
    db.refresh(doc)
    if not doc.vigente or doc.estado != payload.estado_anterior:
        fail("El documento cambió; actualiza antes de revisar.", 409)
    if payload.estado == 'observado' and not payload.comentarios.strip():
        fail("Describe la corrección requerida.", 422)
    before = doc.estado
    doc.estado, doc.comentarios = payload.estado, payload.comentarios.strip()
    audit(team, user, 'revision_documento', documento_id=str(doc.id), anterior=before, estado=doc.estado, comentarios=doc.comentarios)
    db.commit()
    return team_view(db, team, source, True)


@router.put('/integrantes/{key}/diploma')
def diploma(key: UUID, payload: DiplomaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    member = record(db, IntegranteInnovaTec, key)
    team, source = team_access(db, user, member.equipo_id)
    db.refresh(member)
    if member.diploma_estado != payload.estado_anterior or member.diploma_fecha != payload.fecha_anterior:
        fail("La entrega cambió; actualiza el listado antes de continuar.", 409)
    if not member.vigente:
        fail("El integrante ya no está vigente.", 409)
    if payload.estado != 'pendiente':
        if not any(entry.get('estado') in ('etapa_local', 'acreditado', 'etapa_regional', 'etapa_nacional') for entry in team.historial):
            fail("El diploma requiere participación en la etapa local o posterior.", 409)
        # Confirm that the institutional document can be rendered before changing its status.
        build_innovatec_diploma(team, db.get(ConvocatoriaInnovaTec, team.convocatoria_id), source, member)
    member.diploma_estado, member.diploma_fecha = payload.estado, payload.fecha
    audit(team, user, 'diploma', integrante_id=str(member.id), estado=member.diploma_estado, fecha=payload.fecha.isoformat() if payload.fecha else None)
    db.commit()
    return team_view(db, team, source, True)


@router.get('/integrantes/{key}/diploma.pdf')
def diploma_pdf(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    member = record(db, IntegranteInnovaTec, key)
    team, source = team_access(db, user, member.equipo_id, lock=False)
    if not member.vigente or member.diploma_estado not in ('generado', 'entregado'):
        fail("Coordinación debe confirmar la generación del diploma antes de descargarlo.", 409)
    content = build_innovatec_diploma(team, db.get(ConvocatoriaInnovaTec, team.convocatoria_id), source, member)
    return download_response(content, 'application/pdf', f'diploma-innovatec-{member.id}.pdf')


@router.post('/equipos/{key}/canalizar')
def incubator_referral(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    team, source = team_access(db, user, key)
    if team.proyecto_id:
        return {'proyecto_id': str(team.proyecto_id), 'existente': True}
    if team.estado not in ('acreditado', 'etapa_regional', 'etapa_nacional'):
        fail("Canaliza un equipo acreditado con potencial de negocio.", 409)
    owner = record(db, Usuario, source.user)
    if owner.rol != RolUsuario.estudiante:
        fail("El responsable requiere acceso de emprendedor a la Incubadora.", 409)
    project = Proyecto(id=uuid4(), usuario_id=source.user, nombre=source.datos['nombre'], descripcion=source.datos['descripcion'], estatus='En revisión', progreso=0, siguiente_paso='Diagnóstico inicial desde InnovaTec')
    db.add(project)
    db.flush()
    team.proyecto_id = project.id
    audit(team, user, 'canalizacion_incubadora', proyecto_id=str(project.id))
    db.add(HistorialEstatus(proyecto_id=project.id, cambiado_por_id=user.id, estatus_anterior=None, estatus_nuevo='En revisión', comentario=f'Canalizado desde InnovaTec: {team.folio}'))
    db.commit()
    return {'proyecto_id': str(project.id), 'existente': False}


@router.get('/diplomas')
def diploma_list(anio: int | None = Query(None, ge=2000, le=2100), estado: Literal['pendiente', 'generado', 'entregado'] | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    query = select(IntegranteInnovaTec, EquipoInnovaTec, Innovacion, ConvocatoriaInnovaTec).join(EquipoInnovaTec, IntegranteInnovaTec.equipo_id == EquipoInnovaTec.id).join(Innovacion, EquipoInnovaTec.innovacion_id == Innovacion.id).join(ConvocatoriaInnovaTec, EquipoInnovaTec.convocatoria_id == ConvocatoriaInnovaTec.id).where(IntegranteInnovaTec.vigente)
    if anio:
        query = query.where(ConvocatoriaInnovaTec.anio == anio)
    if estado:
        query = query.where(IntegranteInnovaTec.diploma_estado == estado)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = db.execute(query.order_by(ConvocatoriaInnovaTec.anio.desc(), IntegranteInnovaTec.nombre).offset(offset).limit(limit)).all()
    return {'total': total, 'items': [{**serialized(m), 'folio': t.folio, 'proyecto': p.datos['nombre'], 'anio': c.anio} for m, t, p, c in rows]}


@public.get('/platicas')
def public_talks(db: Session = Depends(get_db)):
    rows = db.scalars(select(PlaticaInnovaTec).join(Evento).where(Evento.estatus == 'Activo').order_by(Evento.fecha.desc())).all()
    counts = dict(db.execute(select(Inscripcion.event, func.count()).where(Inscripcion.event.in_([p.evento_id for p in rows]), Inscripcion.estatus == 'Confirmada').group_by(Inscripcion.event)).all())
    return [{**serialized(p), 'evento': serialized(db.get(Evento, p.evento_id)), 'inscritos': counts.get(p.evento_id, 0)} for p in rows]


@router.get('/platicas')
def talks(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    return [{**serialized(p), 'evento': serialized(db.get(Evento, p.evento_id))} for p in db.scalars(select(PlaticaInnovaTec))]


@router.put('/platicas/{key}')
def save_talk(key: UUID, payload: PlaticaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = db.scalar(select(PlaticaInnovaTec).where(PlaticaInnovaTec.id == key).with_for_update())
    if row and payload.evento_id not in (None, row.evento_id):
        fail("Conserva el evento vinculado para proteger sus inscripciones.", 409)
    event = record(db, Evento, row.evento_id, lock=True) if row else record(db, Evento, payload.evento_id, lock=True) if payload.evento_id else None
    if event and db.scalar(select(PlaticaInnovaTec.id).where(PlaticaInnovaTec.evento_id == event.id, PlaticaInnovaTec.id != key)):
        fail("El evento ya tiene una plática vinculada; edítala sin duplicar inscripciones.", 409)
    event_id = event.id if event else uuid4()
    event, values = save_events(db, user, event_id, payload.evento.model_dump(), event, payload.evento.model_dump(), event is None, 'events')
    if event is None:
        event = Evento(id=event_id, **values)
        db.add(event)
    else:
        for name, value in values.items():
            setattr(event, name, value)
    db.flush()
    if row is None:
        row = PlaticaInnovaTec(id=key, evento_id=event_id)
        db.add(row)
    row.publico, row.contenido, row.sede = payload.publico, payload.contenido, payload.sede
    db.commit()
    return {**serialized(row), 'evento': serialized(event)}
