from datetime import date, datetime, timezone
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from typing import Literal
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.auth.security import get_current_user
from app.database import get_db
from app.models import Usuario, Evento, Publication, PiezaDifusion, VisitaSalon, PlantillaMensaje, EnvioMensaje, PreguntaFrecuente, ConfiguracionEnlaces, ConfiguracionIncubadora, ContactoInstitucional, FichaEvento
from app.schemas.enlaces import PiezaInput, VisitaInput, PlantillaInput, EnvioInput, FAQInput, ConfiguracionEnlacesInput, ContactoInput, ContactoReview, FichaEventoInput
from app.modules.compartido.services import admin, require_admin, record, fail, today, has_started, serialized
from app.modules.compartido.editorial_media import galleries, visible
from app.modules.innovacion.services import audit, check_version
from app.auth.rate_limit import public_attempt

router = APIRouter(prefix='/portal/difusion', tags=['Difusión y vinculación'])
public = APIRouter(prefix='/public/enlaces', tags=['Enlaces públicos'])
MODELS = {'piezas': PiezaDifusion, 'visitas': VisitaSalon, 'plantillas': PlantillaMensaje, 'preguntas': PreguntaFrecuente, 'fichas': FichaEvento}


def private_view(row):
    result = serialized(row)
    if isinstance(row, (PlantillaMensaje, EnvioMensaje)):
        result['contenido'] = row.contenido
    return result


@router.get('/configuracion')
def config(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = db.scalar(select(ConfiguracionEnlaces).where(ConfiguracionEnlaces.singleton == 1))
    return private_view(row) if row else {'version': 0, 'vinculacion': '', 'contactos': {}}


@public.get('/configuracion')
def public_config(db: Session = Depends(get_db)):
    row = db.scalar(select(ConfiguracionEnlaces).where(ConfiguracionEnlaces.singleton == 1))
    privacy = db.get(ConfiguracionIncubadora, 1)
    return {'vinculacion': row.vinculacion if row else '', 'contactos': row.contactos if row else {}, 'aviso_privacidad': privacy.aviso_privacidad if privacy and privacy.aviso_aprobado else '[Por definir: aviso institucional aprobado]', 'aviso_aprobado': bool(privacy and privacy.aviso_aprobado), 'version_aviso': privacy.version if privacy else 0}


@router.put('/configuracion')
def save_config(payload: ConfiguracionEnlacesInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    record(db, Usuario, user.id, lock=True)
    row = db.scalar(select(ConfiguracionEnlaces).where(ConfiguracionEnlaces.singleton == 1).with_for_update())
    previous = {key: value for key, value in private_view(row).items() if key != 'historial'} if row else None
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('La configuración no existe.', 404)
    else:
        row = ConfiguracionEnlaces(id=uuid4(), singleton=1, version=0, historial=[])
        db.add(row)
    row.vinculacion, row.contactos = payload.vinculacion, payload.contactos.model_dump()
    audit(row, user, 'configuracion_enlaces', anterior=previous)
    db.commit()
    return private_view(row)


def save(db, user, model, key, payload):
    require_admin(user)
    row = db.scalar(select(model).where(model.id == key).with_for_update())
    previous = {field: value for field, value in private_view(row).items() if field != 'historial'} if row else None
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('El registro no existe.', 404)
    else:
        row = model(id=key, version=0, historial=[])
        db.add(row)
    for field, value in payload.model_dump(exclude={'version'}).items():
        setattr(row, field, value)
    audit(row, user, 'difusion', entidad=model.__tablename__, anterior=previous)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        fail('El registro o su vínculo ya existe. Actualiza la lista antes de guardar.', 409)
    return private_view(row)


def coordinator(db, key):
    person = record(db, Usuario, key)
    if not admin(person):
        fail('Selecciona un responsable con permisos de coordinación.', 422)


@router.put('/piezas/{key}')
def save_piece(key: UUID, payload: PiezaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    coordinator(db, payload.responsable_id)
    if payload.estado == 'publicada' and payload.fecha > today():
        fail('Una pieza publicada no puede tener fecha futura.', 422)
    if payload.publicacion_id:
        record(db, Publication, payload.publicacion_id)
    return save(db, user, PiezaDifusion, key, payload)


@router.put('/visitas/{key}')
def save_visit(key: UUID, payload: VisitaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    coordinator(db, payload.responsable_id)
    if payload.fecha > today():
        fail('La visita realizada no puede tener fecha futura.', 422)
    return save(db, user, VisitaSalon, key, payload)


@router.put('/plantillas/{key}')
def save_template(key: UUID, payload: PlantillaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return save(db, user, PlantillaMensaje, key, payload)


@router.get('/envios')
def send_listing(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    total = db.scalar(select(func.count()).select_from(EnvioMensaje))
    return {'total': total, 'items': [private_view(row) for row in db.scalars(select(EnvioMensaje).order_by(EnvioMensaje.fecha.desc(), EnvioMensaje.id).offset(offset).limit(limit))]}


@router.post('/envios/{key}', status_code=201)
def register_send(key: UUID, payload: EnvioInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    template = record(db, PlantillaMensaje, payload.plantilla_id, lock=True)
    coordinator(db, payload.responsable_id)
    if payload.fecha > today():
        fail('La fecha de un envío registrado no puede ser futura.', 422)
    previous = db.get(EnvioMensaje, key)
    if previous:
        if all(getattr(previous, field) == value for field, value in payload.model_dump().items()):
            return private_view(previous)
        fail('El envío ya está registrado; conserva su evidencia original.', 409)
    if not template.activa:
        fail('Selecciona una plantilla activa.', 422)
    row = EnvioMensaje(id=key, contenido=template.contenido, version=0, historial=[], **payload.model_dump())
    audit(row, user, 'registro_manual_envio', plantilla_version=template.version)
    db.add(row)
    db.commit()
    return private_view(row)


@router.put('/preguntas/{key}')
def save_faq(key: UUID, payload: FAQInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    return save(db, user, PreguntaFrecuente, key, payload)


@public.get('/preguntas')
def public_faq(seccion: Literal['incubadora', 'innovatec'], db: Session = Depends(get_db)):
    return [{key: value for key, value in private_view(row).items() if key != 'historial'} for row in db.scalars(select(PreguntaFrecuente).where(PreguntaFrecuente.activa, PreguntaFrecuente.seccion == seccion).order_by(PreguntaFrecuente.orden, PreguntaFrecuente.id))]


@public.get('/difusion')
def published(db: Session = Depends(get_db)):
    rows = db.scalars(select(PiezaDifusion).where(PiezaDifusion.visible, PiezaDifusion.estado == 'publicada', PiezaDifusion.fecha <= today()).order_by(PiezaDifusion.fecha.desc()).limit(50)).all()
    result = []
    for row in rows:
        news = db.get(Publication, row.publicacion_id) if row.publicacion_id else None
        # Draft/expired news must not leak through a dissemination record.
        if news and not visible(news):
            continue
        result.append({field: getattr(row, field) for field in ('id', 'titulo', 'tipo', 'canal', 'fecha', 'enlace', 'publicacion_id')})
    return result


@public.post('/contacto/{key}', status_code=201)
def contact(key: UUID, payload: ContactoInput, request: Request, db: Session = Depends(get_db)):
    public_attempt('contacto', request.client.host if request.client else 'unknown')
    privacy = db.scalar(select(ConfiguracionIncubadora).where(ConfiguracionIncubadora.id == 1).with_for_update())
    if not privacy or not privacy.aviso_aprobado:
        fail('El contacto estará disponible al publicar el aviso institucional aprobado.', 409)
    if privacy.version != payload.version_aviso:
        fail('El aviso cambió. Revísalo antes de enviar.', 409)
    row = db.get(ContactoInstitucional, key)
    values = payload.model_dump(exclude={'acepto_privacidad', 'version_aviso'})
    if row:
        if all(getattr(row, field) == value for field, value in values.items()):
            return {'id': str(row.id), 'recibido': True}
        fail('El folio ya fue registrado; no se puede reemplazar el mensaje.', 409)
    row = ContactoInstitucional(id=key, version=1, historial=[], consentimiento={'texto': privacy.aviso_privacidad, 'version': privacy.version, 'fecha': datetime.now(timezone.utc).isoformat()}, estado='nuevo', nota='', **values)
    db.add(row)
    db.commit()
    return {'id': str(key), 'recibido': True}


@router.get('/contactos')
def inbox(estado: Literal['nuevo', 'atendido'] | None = None, offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    query = select(ContactoInstitucional)
    if estado:
        query = query.where(ContactoInstitucional.estado == estado)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    return {'total': total, 'items': [{field: value for field, value in private_view(row).items() if field != 'consentimiento'} for row in db.scalars(query.order_by(ContactoInstitucional.creado_en.desc()).offset(offset).limit(limit))]}


@router.put('/contactos/{key}')
def review_contact(key: UUID, payload: ContactoReview, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = record(db, ContactoInstitucional, key, lock=True)
    check_version(row, payload.version)
    previous = row.estado
    row.estado, row.nota = payload.estado, payload.nota
    audit(row, user, 'atencion_contacto', anterior=previous, estado=row.estado)
    db.commit()
    return {'id': str(row.id), 'estado': row.estado, 'version': row.version}


@router.put('/fichas/{key}')
def save_event_details(key: UUID, payload: FichaEventoInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    previous = db.get(FichaEvento, key)
    if previous and previous.evento_id and payload.evento_id != previous.evento_id:
        fail('Conserva el evento vinculado para proteger sus inscripciones y enlaces existentes.', 409)
    if payload.evento_id:
        record(db, Evento, payload.evento_id)
    return save(db, user, FichaEvento, key, payload)


@router.post('/fichas/propuesta')
def event_proposals(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    record(db, Usuario, user.id, lock=True)
    for title, description, slogan in [('Día de Enlaces', 'Actividad del proceso local de InnovaTec. Fechas y lugar pendientes de definición institucional.', ''), ('Premiación InnovaTecNM 2026', 'Premiación de etapa regional y pase al nacional. Fechas y lugar pendientes de definición institucional.', ''), ('EmpoderaTec 2026', 'Evento del Tecnológico Nacional de México e Instituto Tecnológico de Saltillo. Fechas y lugar pendientes de definición institucional.', 'Si lo crees, lo creas')]:
        key = uuid5(NAMESPACE_URL, f'enlaces-its:evento:{title}')
        if db.get(FichaEvento, key) is None:
            row = FichaEvento(id=key, titulo=title, descripcion=description, lema=slogan, lugar='', publicada=False, version=0, historial=[])
            audit(row, user, 'ficha_evento_propuesta')
            db.add(row)
    db.commit()
    return [private_view(row) for row in db.scalars(select(FichaEvento).order_by(FichaEvento.titulo))]


def event_view(db, row, details=None):
    images = galleries(db, 'event', [row.id]).get(str(row.id), []) if visible(row) else []
    return {'id': str(row.id), 'evento_id': str(row.id), 'nombre': details.titulo if details else row.nombre, 'descripcion': details.descripcion if details else row.descripcion, 'lema': details.lema if details else '', 'lugar': details.lugar if details and details.lugar else '[Por definir: lugar]', 'fecha': row.fecha.isoformat(), 'hora': row.hora.strftime('%H:%M'), 'modalidad': row.modalidad, 'cupo': row.cupo, 'precio': float(row.precio), 'abierto': row.estatus == 'Activo' and not has_started(row.fecha, row.hora), 'imagenes': images}


def announcement(row):
    return {'id': str(row.id), 'evento_id': None, 'nombre': row.titulo, 'descripcion': row.descripcion, 'lema': row.lema, 'lugar': row.lugar or '[Por definir: lugar]', 'fecha': None, 'hora': None, 'abierto': False, 'imagenes': []}


@public.get('/eventos')
def public_events(db: Session = Depends(get_db)):
    details = db.scalars(select(FichaEvento).where(FichaEvento.publicada)).all()
    by_event = {row.evento_id: row for row in details if row.evento_id}
    rows = db.scalars(select(Evento).where(Evento.estatus == 'Activo').order_by(Evento.fecha.desc(), Evento.hora).limit(100)).all()
    return [event_view(db, row, by_event.get(row.id)) for row in rows] + [announcement(row) for row in details if row.evento_id is None]


@public.get('/eventos/{key}')
def public_event(key: UUID, db: Session = Depends(get_db)):
    details = db.get(FichaEvento, key)
    if details:
        if not details.publicada:
            fail('La ficha del evento no está publicada.', 404)
        if details.evento_id is None:
            return announcement(details)
        row = record(db, Evento, details.evento_id)
    else:
        row = record(db, Evento, key)
        details = db.scalar(select(FichaEvento).where(FichaEvento.evento_id == key, FichaEvento.publicada))
    if row.estatus != 'Activo':
        fail('El evento no está publicado.', 404)
    return event_view(db, row, details)


# Register the generic collection route last so it cannot intercept inbox/envíos/configuración.
@router.get('/{collection}')
def listing(collection: Literal['piezas', 'visitas', 'plantillas', 'preguntas', 'fichas'], offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), desde: date | None = None, hasta: date | None = None, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    model = MODELS[collection]
    query = select(model)
    if desde and hasta and desde > hasta:
        fail('La fecha inicial no puede ser posterior a la final.', 422)
    if hasattr(model, 'fecha'):
        if desde:
            query = query.where(model.fecha >= desde)
        if hasta:
            query = query.where(model.fecha <= hasta)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    ordering = (model.fecha.desc(), model.id) if hasattr(model, 'fecha') else (model.id,)
    return {'total': total, 'items': [private_view(row) for row in db.scalars(query.order_by(*ordering).offset(offset).limit(limit))]}
