
from sqlalchemy import select
import base64
from app.config import settings
from app.document_storage import store_bytes
from app.models import Usuario, RolUsuario, Proyecto, Horario, Tutoria, Solicitud, Innovacion
from app.initial_registration import validate_data, merge_files
from app.modules.compartido.registration_metadata import registration_metadata
from app.modules.compartido.services import (
    today,
    has_started,
    fail,
    admin,
    require_admin,
    record,
    registration_event,
)


def save_initial_registrations(db, user, key, values, row, payload, new, collection):
    if row and row.user != user.id and not admin(user):
        fail("No tienes acceso a este registro.", 403)
    if admin(user):
        if new:
            fail("El registro lo inicia el solicitante.", 403)
        # Los campos de coordinación se guardan separados de las respuestas.
        admin_values = {**values["administracion"], "identificacion.numero_solicitantes": row.datos.get("identificacion.numero_solicitantes", "1")}
        count = admin_values.pop("identificacion.numero_solicitantes")
        from app.initial_registration import fields
        allowed = dict(fields({"identificacion.numero_solicitantes": count}, True))
        if any(k not in allowed or len(v) > 5000 for k, v in admin_values.items()):
            fail("Campos de coordinación no válidos.", 422)
        values = {"administracion": admin_values}
    else:
        if row and row.estatus not in ("Borrador", "Correcciones solicitadas"):
            fail("El registro está enviado o aprobado; espera las observaciones de coordinación.", 409)
        if row and (db.scalar(select(Proyecto.id).where(Proyecto.registro_id == key)) or db.scalar(select(Solicitud.id).where(Solicitud.registro_id == key, Solicitud.estatus != "Rechazada"))):
            fail("Este registro ya fue enviado. Conserva sus datos originales.", 409)
        if values["administracion"]:
            fail("La revisión y autorización corresponden a coordinación.", 403)
        complete = values["estatus"] == "Pendiente"
        datos = validate_data({**values["datos"], **registration_metadata(db, row)}, complete)
        archivos = merge_files(datos, row.archivos if row else {}, values["archivos"], complete)
        if settings.document_storage == "s3":
            # Existing local annexes migrate on the next successful applicant save.
            for file_key, item in archivos.items():
                if "data" in item:
                    content = base64.b64decode(item["data"])
                    stored = store_bytes(db, content, item["tipo"], f"registrations/{key}")
                    archivos[file_key] = {k: v for k, v in item.items() if k != "data"}
                    archivos[file_key].update(bucket=stored["bucket"], key=stored["key"], size=len(content))
        next_status = "Pendiente" if complete else row.estatus if row else "Borrador"
        trail = list(row.historial or []) if row else []
        if not row or next_status != row.estatus:
            trail.append(registration_event(user, row.estatus if row else None, next_status, "Registro enviado a coordinación." if complete else "Borrador creado."))
        values = {"user": user.id, "datos": datos, "archivos": archivos, "estatus": next_status, "historial": trail}

    return row, values


def save_appointments(db, user, key, values, row, payload, new, collection):
    if user.rol == RolUsuario.externo:
        fail("Las tutorías requieren ser emprendedor.", 403)
    if new:
        record(db, Usuario, user.id, lock=True)
    slot = record(db, Horario, values["slot"], lock=True)
    if new:
        if values["estatus"] != "Confirmada" or has_started(slot.fecha, slot.inicio):
            fail("Selecciona un horario vigente.")
        coordinator = record(db, Usuario, slot.coordinador)
        if coordinator.rol != RolUsuario.admin:
            fail("El coordinador de este horario ya no está disponible.", 409)
        if db.scalar(select(Tutoria.id).where(Tutoria.slot == slot.id, Tutoria.estatus == "Confirmada").limit(1)):
            fail("El horario ya fue reservado.", 409)
        overlapping = db.scalar(select(Tutoria.id).join(Horario, Tutoria.slot == Horario.id).where(
            Tutoria.user == user.id, Tutoria.estatus == "Confirmada", Horario.fecha == slot.fecha,
            Horario.inicio < slot.fin, Horario.fin > slot.inicio).limit(1))
        if overlapping:
            fail("Ya tienes una tutoría que coincide con este horario.", 409)
        values["user"] = user.id
    else:
        if not admin(user) and row.user != user.id:
            fail("No puedes modificar esta tutoría.", 403)
        if values["slot"] != row.slot or row.estatus != "Confirmada" or values["estatus"] not in ("Cancelada", "Completado"):
            fail("La transición de esta tutoría no es válida.")
        if values["estatus"] == "Completado":
            require_admin(user)

    return row, values


def save_innovation(db, user, key, values, row, payload, new, collection):
    if user.rol == RolUsuario.externo or (row and not admin(user) and row.user != user.id):
        fail("No tienes acceso a esta propuesta.", 403)
    previous = row.datos.get("estatus", "Borrador") if row else None
    expected = values.pop("estatus_anterior")
    observations = values.pop("observaciones").strip()
    trail = list(row.datos.get("historial", [])) if row else []
    if row and expected != previous:
        fail("La propuesta cambió. Actualiza los datos antes de continuar.", 409)
    if admin(user):
        if new:
            fail("La propuesta la inicia el emprendedor.", 403)
        allowed = {
            "En revisión": {"Aprobada", "Rechazada", "Correcciones solicitadas"},
            "Aprobada": {"Aprobada"},
        }
        if values["estatus"] not in allowed.get(previous, set()):
            fail("Solo se pueden resolver propuestas enviadas o avanzar las aprobadas.", 409)
        if values["estatus"] in ("Rechazada", "Correcciones solicitadas") and not observations:
            fail("Indica las observaciones para el equipo.", 422)
        stages = ["Local", "Regional", "Nacional"]
        current_stage = row.datos.get("etapa", "Local")
        if values["estatus"] != "Aprobada" and values["etapa"] != current_stage:
            fail("Aprueba la propuesta antes de cambiar su etapa.", 409)
        if stages.index(values["etapa"]) < stages.index(current_stage) or stages.index(values["etapa"]) > stages.index(current_stage) + 1:
            fail("Avanza una etapa a la vez, sin retroceder.", 409)
        # Coordinación revisa; las respuestas pertenecen al solicitante.
        values = {**row.datos, "estatus": values["estatus"], "etapa": values["etapa"], "observaciones": observations}
    else:
        if previous not in (None, "Borrador", "Correcciones solicitadas"):
            fail("Esta propuesta ya fue enviada; espera la revisión de coordinación.", 409)
        if values["estatus"] not in ("Borrador", "En revisión"):
            fail("La autorización corresponde a coordinación.", 403)
        # Serializa las altas del mismo usuario para evitar duplicados simultáneos.
        record(db, Usuario, user.id, lock=True)
        proposals = db.scalars(select(Innovacion).where(Innovacion.user == user.id, Innovacion.id != key))
        if any(p.datos.get("nombre", "").casefold() == values["nombre"].casefold()
               and p.datos.get("modulo") == values["modulo"] and p.datos.get("categoria") == values["categoria"] for p in proposals):
            fail("Ya existe una propuesta con ese nombre en esta categoría.", 409)
        if row and (values["modulo"] != row.datos["modulo"] or values["categoria"] != row.datos["categoria"]):
            fail("Conserva el evento y la categoría de la propuesta.", 409)
        if previous == "Correcciones solicitadas" and values["estatus"] == "Borrador":
            values["estatus"] = previous
        values.update(etapa="Local", observaciones=row.datos.get("observaciones", "") if row else "")
    if previous != values["estatus"] or (row and row.datos.get("etapa") != values["etapa"]):
        event = registration_event(user, previous, values["estatus"], values["observaciones"] if admin(user) else "Propuesta enviada a revisión." if values["estatus"] == "En revisión" else "Borrador creado.")
        trail.append({**event, "etapa": values["etapa"]})
    values["fecha"] = row.datos["fecha"] if row else today().isoformat()
    values["historial"] = trail
    values = {"datos": values, "user": row.user if row else user.id}

    return row, values
