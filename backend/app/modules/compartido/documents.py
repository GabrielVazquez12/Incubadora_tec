"""Project document upload, correction and coordinator review."""
from typing import Literal
from urllib.parse import quote
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, File, Form, Response, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database import get_db
from app.document_storage import store_bytes, read_bytes
from app.document_validation import MAX_DOCUMENT_BYTES, validate_document
from app.models import Documento, Usuario
from app.modules.compartido.services import project_access, require_admin, record, fail, serialized, registration_event

router = APIRouter(prefix="/portal", tags=["documentos"])


def create_document(db, project, user, name, content, media_type, previous=None):
    stored = store_bytes(db, content, media_type, f"projects/{project.id}")
    doc = Documento(id=uuid4(), proyecto_id=project.id, subido_por_id=user.id,
                    nombre=name, tipo=media_type, bucket=stored["bucket"], clave_archivo=stored["key"],
                    contenido=stored["content"], estatus="Pendiente", observaciones="", vigente=True,
                    reemplaza_id=previous.id if previous else None,
                    historial=[registration_event(user, None, "Pendiente", "Corrección enviada." if previous else "Documento enviado.")])
    if previous:
        previous.vigente = False
    db.add(doc)
    return doc


@router.post("/projects/{key}/documents", status_code=201)
def upload_document(key: UUID, file: UploadFile = File(...), reemplaza_id: UUID | None = Form(None),
                    db: Session = Depends(get_db), user: Usuario = Depends(get_current_user)):
    project = project_access(db, user, key)
    previous = None
    if reemplaza_id:
        previous = record(db, Documento, reemplaza_id, lock=True)
        if previous.proyecto_id != key:
            fail("El documento no pertenece a este proyecto.", 403)
        if not previous.vigente or previous.estatus != "Correcciones solicitadas":
            fail("Solo puedes corregir un documento vigente con observaciones.", 409)
    try:
        content = file.file.read(MAX_DOCUMENT_BYTES + 1)
    finally:
        file.file.close()
    media_type = validate_document(file.filename, content)
    doc = create_document(db, project, user, file.filename, content, media_type, previous)
    db.commit()
    return {"id": str(doc.id)}


class DocumentReview(BaseModel):
    estatus: Literal["Aprobado", "Correcciones solicitadas"]
    estatus_anterior: Literal["Pendiente", "Aprobado", "Correcciones solicitadas"]
    observaciones: str = Field(default="", max_length=2000)


@router.post("/documents/{key}/review")
def review_document(key: UUID, payload: DocumentReview, db: Session = Depends(get_db),
                    user: Usuario = Depends(get_current_user)):
    require_admin(user)
    doc = record(db, Documento, key, lock=True)
    if not doc.vigente or doc.estatus != payload.estatus_anterior or doc.estatus == payload.estatus:
        fail("El documento cambió. Actualiza los datos antes de continuar.", 409)
    comment = payload.observaciones.strip()
    if payload.estatus == "Correcciones solicitadas" and not comment:
        fail("Indica qué debe corregir el emprendedor.", 422)
    doc.historial = [*doc.historial, registration_event(user, doc.estatus, payload.estatus, comment)]
    doc.estatus, doc.observaciones = payload.estatus, comment
    db.commit()
    return {"id": str(doc.id), "estatus": doc.estatus}


def download_response(content, media_type, name):
    return Response(content=content, media_type=media_type, headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(name, safe=""),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})
