from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import Field
from sqlalchemy import select, func
from sqlalchemy.orm import Session, defer
from app.auth.security import get_current_user
from app.database import get_db
from app.models import Usuario, RolUsuario, PerfilAcceso, AuditoriaAcceso, ExpedienteIncubadora, Proyecto, Documento
from app.access import require_manager, advisor_project, profile
from app.schemas.incubadora import VersionInput
from app.schemas.portal import Description
from app.modules.compartido.services import fail, record, serialized
from app.modules.innovacion.services import audit, check_version
from app.modules.incubadora.routes import dossier_view

router = APIRouter(prefix='/portal/gobierno', tags=['Perfiles y auditoría'])


class PerfilInput(VersionInput):
    perfil: Literal['asesor', 'administrador', 'sin_perfil']
    motivo: Description = Field(max_length=500)


@router.get('/perfiles')
def profiles(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_manager(db, user)
    assigned_profiles = {row.usuario_id: row for row in db.scalars(select(PerfilAcceso))}
    return [{**serialized(person), 'perfil': assigned_profiles[person.id].perfil if person.id in assigned_profiles else 'sin_perfil', 'version_perfil': assigned_profiles[person.id].version if person.id in assigned_profiles else 0} for person in db.scalars(select(Usuario).order_by(Usuario.nombre))]


@router.put('/perfiles/{key}')
def save_profile(key: UUID, payload: PerfilInput, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    # All capability mutations share these locks, including the first administrator.
    list(db.scalars(select(Usuario).where(Usuario.rol == RolUsuario.admin).order_by(Usuario.id).with_for_update()))
    require_manager(db, user)
    person = record(db, Usuario, key, lock=True)
    row = db.get(PerfilAcceso, key)
    if row:
        check_version(row, payload.version)
    elif payload.version:
        fail('El perfil aún no existe.', 409)
    if payload.perfil == 'administrador' and person.rol != RolUsuario.admin:
        fail('El perfil Administrador requiere una cuenta administrativa existente.', 422)
    if payload.perfil == 'asesor' and person.rol == RolUsuario.admin:
        fail('Coordinación ya dispone de acceso a los expedientes.', 422)
    if row and row.perfil == 'administrador' and payload.perfil != 'administrador':
        others = db.scalar(select(func.count()).select_from(PerfilAcceso).where(PerfilAcceso.perfil == 'administrador', PerfilAcceso.usuario_id != key))
        if not others:
            fail('Conserva al menos un Administrador activo.', 409)
    if row is None:
        row = PerfilAcceso(usuario_id=key, perfil='sin_perfil', version=0, historial=[])
        db.add(row)
    previous = row.perfil
    row.perfil = payload.perfil
    audit(row, user, 'perfil_complementario', anterior=previous, perfil=row.perfil, motivo=payload.motivo)
    person.auth_version += 1
    db.commit()
    return {'perfil': row.perfil, 'version': row.version, 'requiere_login': key == user.id}


@router.get('/auditoria')
def audit_listing(offset: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200), db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    require_manager(db, user)
    return {'total': db.scalar(select(func.count()).select_from(AuditoriaAcceso)), 'items': [serialized(row) for row in db.scalars(select(AuditoriaAcceso).order_by(AuditoriaAcceso.fecha.desc(), AuditoriaAcceso.id).offset(offset).limit(limit))]}


@router.get('/expedientes')
def assigned_dossiers(db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    if profile(db, user) != 'asesor':
        fail('Esta consulta requiere el perfil Asesor.', 403)
    return [{'id': str(project.id), 'nombre': project.nombre, 'estado': folder.estado, 'proxima_revision': folder.proxima_revision} for project, folder in db.execute(select(Proyecto, ExpedienteIncubadora).join(ExpedienteIncubadora, ExpedienteIncubadora.proyecto_id == Proyecto.id).where(ExpedienteIncubadora.asesor_id == user.id).order_by(Proyecto.nombre))]


@router.get('/expedientes/{key}')
def assigned_dossier(key: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = advisor_project(db, user, key)
    result = dossier_view(db, project, user)
    result['documentos'] = [{field: getattr(row, field) for field in ('id', 'nombre', 'tipo', 'estatus', 'vigente', 'observaciones')} for row in db.scalars(select(Documento).options(defer(Documento.contenido)).where(Documento.proyecto_id == key))]
    return result


@router.get('/expedientes/{key}/documentos/{document_id}')
def advisor_document(key: UUID, document_id: UUID, db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    advisor_project(db, user, key)
    document = record(db, Documento, document_id)
    if document.proyecto_id != key:
        fail('El documento no pertenece al expediente asignado.', 403)
    from app.document_storage import read_bytes
    from app.modules.compartido.documents import download_response
    return download_response(read_bytes(document.bucket, document.clave_archivo, document.contenido), document.tipo, document.nombre)
