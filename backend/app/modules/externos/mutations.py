
from sqlalchemy import select
from app.models import Usuario, RolUsuario, Proyecto, IntegranteProyecto, HistorialEstatus, RegistroInicial
from app.modules.compartido.services import (
    today,
    fail,
    admin,
    record,
    serialized,
    validate_initial_registration,
    completed_registration,
    registration_summary,
    registration_event,
)


def save_requests(db, user, key, values, row, payload, new, collection):
    observations = values.pop("observaciones", "").strip()
    if not admin(user):
        validate_initial_registration(values)
        source = completed_registration(db, user.id, values.get("registro_id"))
        if row and row.registro_id and values["registro_id"] != row.registro_id:
            fail("Conserva el registro de origen de la solicitud.", 409)
        values.update(registration_summary(source))
    if admin(user):
        if new or row.estatus != "En revisión" or values["estatus"] not in ("Aprobada", "Rechazada"):
            fail("Solo se pueden resolver solicitudes pendientes.")
        values = {"estatus": values["estatus"]}
        if values["estatus"] == "Rechazada":
            if not observations:
                fail("Indica el motivo del rechazo y los ajustes necesarios.", 422)
            if row.registro_id:
                source = record(db, RegistroInicial, row.registro_id, lock=True)
                if db.scalar(select(Proyecto.id).where(Proyecto.registro_id == source.id).limit(1)):
                    fail("El registro ya tiene un proyecto; conserva su aprobación.", 409)
                previous = source.estatus
                source.estatus = "Correcciones solicitadas"
                source.observaciones = observations
                source.historial = [*(source.historial or []), registration_event(
                    user, previous, source.estatus, observations)]
        if values["estatus"] == "Aprobada":
            validate_initial_registration(serialized(row))
            completed_registration(db, row.user, row.registro_id)
            applicant = record(db, Usuario, row.user, lock=True)
            if applicant.rol != RolUsuario.externo:
                fail("El solicitante ya cambió de rol.")
            applicant.rol = RolUsuario.estudiante
            applicant.especialidad = row.especialidad
            project = Proyecto(nombre=row.nombre, descripcion=row.descripcion, producto_servicio=row.producto_servicio, telefono=row.telefono, solicitud_id=row.id, registro_id=row.registro_id, especialidad=row.especialidad, usuario_id=row.user, estatus="Pendiente", progreso=0)
            db.add(project)
            db.flush()
            db.add(IntegranteProyecto(proyecto_id=project.id, usuario_id=row.user))
            db.add(HistorialEstatus(proyecto_id=project.id, cambiado_por_id=user.id, estatus_nuevo="Pendiente", comentario="Solicitud de ingreso aprobada"))
    else:
        if user.rol != RolUsuario.externo or (row and (row.user != user.id or row.estatus != "Rechazada")):
            fail("No puedes modificar esta solicitud.", 403)
        values.update(user=user.id, fecha=today(), estatus="En revisión")

    return row, values
