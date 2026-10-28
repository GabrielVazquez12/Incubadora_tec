from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import hmac
from uuid import UUID, uuid4, uuid5, NAMESPACE_URL
from fastapi import APIRouter, Depends, Request, Response, Query
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.auth.security import get_current_user
from app.models import Usuario, Encuesta, PreguntaEncuesta, RespuestaEncuesta, ConfiguracionIncubadora
from app.schemas.encuestas import EncuestaInput, PreguntaInput, RespuestaInput
from app.modules.compartido.services import require_admin, record, fail, serialized, today
from app.modules.innovacion.services import audit, check_version
from app.schemas.incubadora import NECESIDADES

router = APIRouter(prefix='/portal/encuestas', tags=['Encuestas'])
public = APIRouter(prefix='/public/encuestas', tags=['Encuestas públicas'])
optional_token = OAuth2PasswordBearer(tokenUrl='/auth/login', auto_error=False)
COOKIE = 'enlaces_encuestas'


def cookie_identity(request):
    token = request.cookies.get(COOKIE)
    if not token or len(token) > 2048:
        return None
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return str(UUID(payload['anon'])) if payload.get('purpose') == 'survey' else None
    except (JWTError, KeyError, ValueError, TypeError):
        return None


def response_identity(survey_id, identity):
    return hmac.new(settings.jwt_secret.encode(), f'survey:{survey_id}:{identity}'.encode(), sha256).hexdigest()


def questions(db, key):
    return [{'id': str(q.id), **q.datos} for q in db.scalars(select(PreguntaEncuesta).where(PreguntaEncuesta.encuesta_id == key, PreguntaEncuesta.activa).order_by(PreguntaEncuesta.orden))]


def view(db, row, private=False):
    result = {key: value for key, value in serialized(row).items() if private or key != 'historial'}
    result['preguntas'] = questions(db, row.id)
    if private:
        result['respuestas'] = db.scalar(select(func.count()).select_from(RespuestaEncuesta).where(RespuestaEncuesta.encuesta_id == row.id))
    return result


@router.get('')
def listing(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    return [view(db, row, True) for row in db.scalars(select(Encuesta).order_by(Encuesta.titulo))]


@public.get('')
def public_listing(db: Session = Depends(get_db)):
    return [{key: value for key, value in view(db, row).items() if key not in ('preguntas', 'privacidad')} for row in db.scalars(select(Encuesta).where(Encuesta.publicada).order_by(Encuesta.apertura.desc()))]


@public.get('/{key}')
def public_survey(key: UUID, request: Request, response: Response, db: Session = Depends(get_db)):
    row = record(db, Encuesta, key)
    if not row.publicada:
        fail('La encuesta no está publicada.', 404)
    identity = cookie_identity(request)
    if row.anonima and identity is None:
        identity = str(uuid4())
        token = jwt.encode({'anon': identity, 'purpose': 'survey', 'exp': datetime.now(timezone.utc) + timedelta(days=365)}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        response.set_cookie(COOKIE, token, max_age=365 * 86400, httponly=True, samesite='lax', secure=request.url.hostname not in ('localhost', '127.0.0.1'), path='/')
    responded = bool(row.anonima and db.scalar(select(RespuestaEncuesta.id).where(RespuestaEncuesta.encuesta_id == key, RespuestaEncuesta.identidad == response_identity(key, identity))))
    response.headers['Cache-Control'] = 'no-store'
    return {**view(db, row), 'abierta': row.apertura <= today() <= row.cierre, 'respondida': responded}


@router.put('/{key}')
def save_survey(key: UUID, payload: EncuestaInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = db.scalar(select(Encuesta).where(Encuesta.id == key).with_for_update())
    submitted = [q.model_dump(mode='json') for q in payload.preguntas]
    previous = {field: value for field, value in view(db, row).items() if field != 'privacidad'} if row else None
    if row:
        check_version(row, payload.version)
        has_answers = bool(db.scalar(select(RespuestaEncuesta.id).where(RespuestaEncuesta.encuesta_id == key).limit(1)))
        if has_answers and (submitted != questions(db, key) or payload.anonima != row.anonima or payload.publico != row.publico):
            fail('La encuesta tiene respuestas. Conserva preguntas, público y anonimato; crea otra para modificar el diseño.', 409)
    elif payload.version:
        fail('La encuesta no existe.', 404)
    else:
        row = Encuesta(id=key, version=0, historial=[])
        db.add(row)
    privacy = db.get(ConfiguracionIncubadora, 1)
    if payload.publicada and not payload.anonima and (not privacy or not privacy.aviso_aprobado):
        fail('Configura el aviso institucional aprobado antes de publicar una encuesta identificada.', 409)
    if payload.publicada and not payload.anonima:
        row.privacidad = {'texto': privacy.aviso_privacidad, 'version': privacy.version}
    else:
        row.privacidad = {}
    for field, value in payload.model_dump(exclude={'version', 'preguntas'}).items():
        setattr(row, field, value)
    existing = db.scalars(select(PreguntaEncuesta).where(PreguntaEncuesta.encuesta_id == key)).all()
    keep = {q.id for q in payload.preguntas}
    for q in existing:
        q.activa = q.id in keep
    db.flush()
    for order, question in enumerate(payload.preguntas):
        q = db.get(PreguntaEncuesta, question.id)
        if q and q.encuesta_id != key:
            fail('No puedes usar preguntas de otra encuesta.', 422)
        if q is None:
            q = PreguntaEncuesta(id=question.id, encuesta_id=key)
            db.add(q)
        q.datos, q.orden, q.activa = question.model_dump(mode='json', exclude={'id'}), order, True
    audit(row, user, 'encuesta', publicada=row.publicada, anterior=previous)
    db.commit()
    return view(db, row, True)


def validate_answers(definitions, values):
    allowed = {q['id'] for q in definitions}
    submitted = {str(key): value for key, value in values.items()}
    if set(submitted) - allowed:
        fail('La respuesta contiene preguntas que no pertenecen a esta encuesta.', 422)
    answers = {}
    for q in definitions:
        value = submitted.get(q['id'])
        if isinstance(value, str):
            value = value.strip()
        empty = value is None or value == '' or value == []
        if empty:
            if q['obligatoria']:
                fail(f'Responde la pregunta obligatoria: {q["titulo"]}.', 422)
            continue
        kind = q['tipo']
        valid = (kind == 'seleccion_unica' and type(value) is str and value in q['opciones'] or kind == 'multiseleccion' and type(value) is list and len(value) == len(set(value)) and all(v in q['opciones'] for v in value) or kind == 'escala' and type(value) is int and q['minimo'] <= value <= q['maximo'] or kind == 'texto' and type(value) is str and len(value) <= 3000)
        if not valid:
            fail(f'La respuesta no tiene el tipo o valor permitido: {q["titulo"]}.', 422)
        answers[q['id']] = value
    return answers


@public.post('/{key}/respuestas', status_code=201)
def respond(key: UUID, payload: RespuestaInput, request: Request, token: str | None = Depends(optional_token), db: Session = Depends(get_db)):
    row = record(db, Encuesta, key, lock=True)
    if not row.publicada or not row.apertura <= today() <= row.cierre:
        fail('La encuesta no está abierta para respuestas.', 409)
    check_version(row, payload.version_encuesta)
    user = None
    if row.anonima:
        identity = cookie_identity(request)
        if identity is None:
            fail('Abre la encuesta y habilita las cookies necesarias antes de responder.', 409)
    else:
        if not token:
            fail('Inicia sesión para responder esta encuesta identificada.', 401)
        user = get_current_user(token, db)
        identity = str(user.id)
        if not payload.acepto_privacidad:
            fail('Acepta el aviso de privacidad de la encuesta.', 422)
    values = validate_answers(questions(db, key), payload.respuestas)
    digest = response_identity(key, identity)
    existing = db.scalar(select(RespuestaEncuesta).where(RespuestaEncuesta.encuesta_id == key, RespuestaEncuesta.identidad == digest))
    if existing:
        if existing.id == payload.id and existing.datos == values:
            return {'id': str(existing.id), 'confirmada': True}
        fail('Ya registraste una respuesta en esta encuesta.', 409)
    if db.get(RespuestaEncuesta, payload.id):
        fail('Este folio de respuesta ya fue utilizado.', 409)
    consent = {'version': row.privacidad.get('version'), 'texto': row.privacidad.get('texto'), 'fecha': datetime.now(timezone.utc).isoformat()} if user else {}
    db.add(RespuestaEncuesta(id=payload.id, encuesta_id=key, usuario_id=user.id if user else None, identidad=digest, datos=values, consentimiento=consent))
    db.commit()
    return {'id': str(payload.id), 'confirmada': True}


@router.get('/{key}/resultados')
def results(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    row = record(db, Encuesta, key)
    responses = db.scalars(select(RespuestaEncuesta).where(RespuestaEncuesta.encuesta_id == key).order_by(RespuestaEncuesta.creado_en)).all()
    results = []
    for q in questions(db, key):
        values = [r.datos[q['id']] for r in responses if q['id'] in r.datos]
        counts = Counter(item for value in values for item in (value if isinstance(value, list) else [value]))
        choices = q['opciones'] if q['tipo'] in ('seleccion_unica', 'multiseleccion') else list(range(q['minimo'], q['maximo'] + 1)) if q['tipo'] == 'escala' else []
        results.append({**q, 'respondidas': len(values), 'distribucion': [{'opcion': choice, 'cantidad': counts[choice], 'porcentaje': round(counts[choice] * 100 / len(values), 2) if values else 0} for choice in choices], 'textos': values if q['tipo'] == 'texto' else []})
    return {'encuesta': view(db, row, True), 'total': len(responses), 'preguntas': results, 'respuestas': [{'id': str(r.id), 'fecha': r.creado_en.isoformat(), 'datos': r.datos} for r in responses], 'nota': 'Porcentajes sobre quienes respondieron cada pregunta. La multiselección puede sumar más de 100%.'}


@router.post('/plantillas')
def templates(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_admin(user)
    for audience in ('alumnos', 'docentes', 'usuarios de la Incubadora'):
        key = uuid5(NAMESPACE_URL, f'enlaces-its:encuesta-propuesta:{audience}')
        if db.get(Encuesta, key):
            continue
        questions_data = [('¿Qué información necesitas para participar?', 'texto', [])] if audience != 'usuarios de la Incubadora' else [('¿Qué necesidades quieres atender?', 'multiseleccion', list(NECESIDADES)), ('¿Qué frecuencia de seguimiento prefieres?', 'seleccion_unica', ['semanal', 'cada 15 días', 'mensual']), ('¿Qué modalidad de asesoría prefieres?', 'seleccion_unica', ['en línea', 'presencial', 'mixta']), ('¿Has detenido o pausado un proyecto?', 'seleccion_unica', ['Sí', 'No'])]
        data = EncuestaInput(titulo=f'Encuesta propuesta: {audience}', descripcion='Propuesta editable sujeta a revisión institucional. No incluye respuestas precargadas.', publico=audience, preguntas=[PreguntaInput(id=uuid4(), titulo=title, tipo=kind, opciones=choices) for title, kind, choices in questions_data])
        save_survey(key, data, db, user)
    return [view(db, row, True) for row in db.scalars(select(Encuesta).order_by(Encuesta.titulo))]
