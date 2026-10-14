"""Capabilities are checked from the database on every request, never from JWT claims."""
from sqlalchemy import select, func
from app.models import PerfilAcceso, ExpedienteIncubadora, RolUsuario
from app.modules.compartido.services import admin, fail, record, serialized


def profile(db, user):
    row = db.get(PerfilAcceso, user.id)
    return row.perfil if row else 'sin_perfil'


def manages_access(db, user):
    if not admin(user):
        return False
    if profile(db, user) == 'administrador':
        return True
    return not db.scalar(select(func.count()).select_from(PerfilAcceso).where(PerfilAcceso.perfil == 'administrador'))


def require_manager(db, user):
    if not manages_access(db, user):
        fail('Esta operación requiere el perfil Administrador.', 403)


def identity(db, user):
    return {**serialized(user), 'perfil': profile(db, user), 'gestiona_accesos': manages_access(db, user)}


def assigned(db, user, project_id):
    return profile(db, user) == 'asesor' and db.scalar(select(ExpedienteIncubadora.proyecto_id).where(ExpedienteIncubadora.proyecto_id == project_id, ExpedienteIncubadora.asesor_id == user.id)) is not None


def advisor_project(db, user, key):
    # Lock the same project as reassignment before checking the current assignment.
    from app.models import Proyecto
    project = record(db, Proyecto, key, lock=True)
    if not admin(user) and not assigned(db, user, key):
        fail('No tienes acceso a este expediente asignado.', 403)
    return project
