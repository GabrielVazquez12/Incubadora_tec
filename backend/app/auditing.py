"""Transaction-bound audit metadata, with no submitted field values or secrets."""
from uuid import UUID, uuid4
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session
from app.models import AuditoriaAcceso

SENSITIVE = {'password_hash', 'auth_version', 'historial'}


@event.listens_for(Session, 'before_flush')
def audit_changes(db, flush_context, instances):
    if any(isinstance(row, AuditoriaAcceso) for row in db.dirty | db.deleted):
        raise ValueError('Los registros de auditoría son de solo lectura.')
    actor = db.info.get('actor_id')
    if actor is None:
        return
    for operation, rows in [('crear', list(db.new)), ('editar', list(db.dirty)), ('eliminar', list(db.deleted))]:
        for row in rows:
            if isinstance(row, AuditoriaAcceso):
                continue
            state = inspect(row)
            fields = [column.key for column in state.mapper.column_attrs if column.key not in SENSITIVE and (operation != 'editar' or state.attrs[column.key].history.has_changes())]
            if operation == 'editar' and 'password_hash' in state.attrs and state.attrs.password_hash.history.has_changes():
                fields.append('credenciales')
            if not fields:
                continue
            for column in state.mapper.primary_key:
                if operation == 'crear' and getattr(row, column.key, None) is None and column.type.python_type is UUID:
                    setattr(row, column.key, uuid4())
            keys = [getattr(row, column.key, None) for column in state.mapper.primary_key]
            key = ':'.join(str(value) for value in keys if value is not None)
            db.add(AuditoriaAcceso(actor_id=actor, entidad=row.__tablename__, registro_id=key or 'nuevo', operacion=operation, campos=fields))
