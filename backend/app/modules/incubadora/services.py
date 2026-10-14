from calendar import monthrange
from datetime import timedelta
from sqlalchemy import select, func
from app.models import Proyecto, RegistroInicial, DiagnosticoIncubadora, ExpedienteIncubadora, Documento, Usuario, IntegranteProyecto, Avance, Tarea
from app.modules.compartido.services import admin, fail, record, project_access, today, serialized
from app.modules.innovacion.services import audit, check_version

STATES = {
    'activo': ('en_seguimiento', 'pausado', 'concluido', 'formalizado'),
    'en_seguimiento': ('activo', 'pausado', 'concluido', 'formalizado'),
    'pausado': ('activo',), 'concluido': ('activo',), 'formalizado': ('activo',),
}


def next_review(day, frequency):
    if frequency == 'semanal':
        return day + timedelta(days=7)
    if frequency == 'cada 15 días':
        return day + timedelta(days=15)
    if frequency == 'mensual':
        month, year = (1, day.year + 1) if day.month == 12 else (day.month + 1, day.year)
        return day.replace(year=year, month=month, day=min(day.day, monthrange(year, month)[1]))
    raise ValueError('Frecuencia de seguimiento no válida.')


def inactive(row, threshold, day):
    return row.estado == 'pausado' or threshold is not None and row.estado not in ('concluido', 'formalizado') and (day - row.ultimo_movimiento).days >= threshold


def expediente(db, project, user, create=False):
    row = db.scalar(select(ExpedienteIncubadora).where(ExpedienteIncubadora.proyecto_id == project.id).with_for_update())
    if row:
        db.refresh(row)
    elif create:
        if project.estatus == 'Completado':
            fail('Coordinación debe reabrir el proyecto anterior antes de iniciar una nueva atención institucional.', 409)
        row = ExpedienteIncubadora(proyecto_id=project.id, estado='activo', ultimo_movimiento=last_movement(db, project), version=0, historial=[])
        audit(row, user, 'apertura_expediente')
        row.version = 0  # First mutation accepts the virtual dossier version shown by GET.
        db.add(row)
        db.flush()
    return row


def last_movement(db, project):
    values = [project.creado_en.date() if project.creado_en else today(), db.scalar(select(func.max(Avance.fecha)).where(Avance.project == project.id)), db.scalar(select(func.max(Tarea.fecha)).where(Tarea.project == project.id))]
    return max(value for value in values if value is not None)


def diagnostic_for(db, project):
    row = db.scalar(select(DiagnosticoIncubadora).where(DiagnosticoIncubadora.proyecto_id == project.id))
    if not row and project.registro_id:
        row = db.scalar(select(DiagnosticoIncubadora).where(DiagnosticoIncubadora.registro_id == project.registro_id))
    return row


def evidence(db, project_id, payload):
    if payload.documento_id:
        document = record(db, Documento, payload.documento_id)
        if document.proyecto_id != project_id:
            fail('La evidencia debe pertenecer al mismo proyecto.', 403)


def responsible(db, project, key):
    person = record(db, Usuario, key)
    member = db.get(IntegranteProyecto, (project.id, key))
    from app.access import assigned
    if not admin(person) and person.id != project.usuario_id and not member and not assigned(db, person, project.id):
        fail('Selecciona un responsable del proyecto o un coordinador.', 422)
    return person


def changed(row, payload, user, action):
    check_version(row, payload.version)
    audit(row, user, action)


def diagnostic_view(row):
    if row is None:
        return None
    return {**serialized(row), 'consentimiento': {key: value for key, value in row.consentimiento.items() if key != 'texto'}}
