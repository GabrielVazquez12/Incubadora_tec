from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import defer
from app.models import Innovacion, EquipoInnovaTec, ConvocatoriaInnovaTec, IntegranteInnovaTec, DocumentoInnovaTec, ArchivoConvocatoriaInnovaTec
from app.modules.compartido.services import admin, record, fail, serialized

TRANSITIONS = {
    "inscrito": {"documentacion_recibida", "baja"},
    "documentacion_recibida": {"etapa_local", "baja"},
    "etapa_local": {"acreditado", "no_acreditado", "baja"},
    "acreditado": {"etapa_regional", "baja"},
    "etapa_regional": {"etapa_nacional", "no_acreditado", "baja"},
    "etapa_nacional": {"no_acreditado", "baja"},
    "no_acreditado": {"baja"}, "baja": set(),
}


def audit(row, user, action, **details):
    row.historial = [*(row.historial or []), {"fecha": datetime.now(timezone.utc).isoformat(), "usuario_id": str(user.id), "responsable": user.nombre, "accion": action, **details}]
    row.version = (row.version or 0) + 1


def team_access(db, user, key, lock=True):
    team = record(db, EquipoInnovaTec, key)
    source = record(db, Innovacion, team.innovacion_id, lock=lock)
    if not admin(user) and source.user != user.id:
        fail("No tienes acceso a este equipo.", 403)
    if lock:
        team = record(db, EquipoInnovaTec, key, lock=True)
        # SQLAlchemy's identity map may retain the pre-lock snapshot while we
        # waited for another transaction. Reload under the acquired locks.
        db.refresh(source)
        db.refresh(team)
    return team, source


def check_version(row, expected):
    if row.version != expected:
        fail("El expediente cambió. Actualiza los datos antes de continuar.", 409)


def file_metadata(row):
    return {k: v for k, v in serialized(row).items() if k not in ("bucket", "clave")}


def convocatoria_view(db, row, private=False):
    result = {"id": str(row.id), "anio": row.anio, "version": row.version, "publicada": row.publicada, **row.datos}
    if private:
        result["historial"] = row.historial
    result["archivos"] = [file_metadata(f) for f in db.scalars(select(ArchivoConvocatoriaInnovaTec).options(defer(ArchivoConvocatoriaInnovaTec.contenido)).where(ArchivoConvocatoriaInnovaTec.convocatoria_id == row.id, ArchivoConvocatoriaInnovaTec.vigente))]
    return result


def team_view(db, team, source, detail=False):
    call = record(db, ConvocatoriaInnovaTec, team.convocatoria_id)
    result = {**serialized(team), "anio": call.anio, "propuesta": {**source.datos, "id": str(source.id)}, "owner": str(source.user)}
    result.pop("consentimiento", None)
    if not detail:
        result.pop("historial", None)
    else:
        result["integrantes"] = [serialized(m) for m in db.scalars(select(IntegranteInnovaTec).where(IntegranteInnovaTec.equipo_id == team.id, IntegranteInnovaTec.vigente).order_by(IntegranteInnovaTec.nombre))]
        result["documentos"] = [file_metadata(f) for f in db.scalars(select(DocumentoInnovaTec).options(defer(DocumentoInnovaTec.contenido)).where(DocumentoInnovaTec.equipo_id == team.id).order_by(DocumentoInnovaTec.creado_en))]
        # Freeze requirements and privacy version to what the team accepted.
        result["requisitos"] = team.consentimiento["requisitos"]
        result["convocatoria"] = {"titulo": call.datos["titulo"], "version_aceptada": team.consentimiento["version"], "version_actual": call.version}
        result["transiciones"] = sorted(TRANSITIONS[team.estado])
    return result


def transition(db, team, user, payload):
    check_version(team, payload.version)
    if payload.estado not in TRANSITIONS[team.estado]:
        fail("La transición de estado no está permitida.", 409)
    if payload.estado not in ("baja", "no_acreditado"):
        documents = {d.requisito: d.estado for d in db.scalars(select(DocumentoInnovaTec).where(DocumentoInnovaTec.equipo_id == team.id, DocumentoInnovaTec.vigente))}
        allowed = {"recibido", "aprobado"} if payload.estado == "documentacion_recibida" else {"aprobado"}
        if any(documents.get(name) not in allowed for name in team.consentimiento["requisitos"]):
            fail("Completa la documentación requerida y resuelve las observaciones antes de avanzar.", 422)
    previous = team.estado
    team.estado = payload.estado
    audit(team, user, "estado", anterior=previous, estado=team.estado, motivo=payload.motivo)
