from datetime import date, datetime
from typing import Annotated, Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StringConstraints, model_validator
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Publication, Evento, RolUsuario
from app.auth.security import require_role
from app.modules.compartido.editorial_media import galleries

router = APIRouter(tags=['boletin'])
admin = Depends(require_role(RolUsuario.admin))


class PublicationInput(BaseModel):
    titulo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    resumen: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    contenido: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=12000)]
    categoria: Literal['Noticia', 'Convocatoria', 'Aviso'] = 'Noticia'
    fecha: date
    vence: date | None = None
    publicada: bool = False
    destacada: bool = False

    @model_validator(mode='after')
    def dates(self):
        if self.vence and self.vence < self.fecha:
            raise ValueError('La fecha de cierre debe ser igual o posterior a la publicación.')
        return self


def serialized(item, images=None):
    return {**{key: getattr(item, key) for key in ['id', 'titulo', 'resumen', 'contenido', 'categoria', 'fecha', 'vence', 'publicada', 'destacada']}, 'imagenes': images or []}


@router.get('/public/newsletter')
def newsletter(db: Session = Depends(get_db)):
    now = datetime.now(ZoneInfo('America/Mexico_City'))
    news = db.scalars(select(Publication).where(Publication.publicada.is_(True), Publication.fecha <= now.date(), or_(Publication.vence.is_(None), Publication.vence >= now.date())).order_by(Publication.destacada.desc(), Publication.fecha.desc(), Publication.id).limit(40)).all()
    events = db.scalars(select(Evento).where(Evento.estatus == 'Activo', or_(Evento.fecha > now.date(), and_(Evento.fecha == now.date(), Evento.hora >= now.time().replace(tzinfo=None)))).order_by(Evento.fecha, Evento.hora).limit(12)).all()
    news_images = galleries(db, 'publication', [n.id for n in news])
    event_images = galleries(db, 'event', [e.id for e in events])
    return {'publicaciones': [serialized(n, news_images.get(str(n.id))) for n in news], 'eventos': [{**{key: getattr(e, key) for key in ['id', 'nombre', 'descripcion', 'tipo', 'fecha', 'hora', 'modalidad', 'precio', 'cupo']}, 'imagenes': event_images.get(str(e.id), [])} for e in events], 'actualizado': now.isoformat()}


@router.get('/admin/publications', dependencies=[admin])
def publications(db: Session = Depends(get_db)):
    items = db.scalars(select(Publication).order_by(Publication.fecha.desc(), Publication.id)).all()
    images = galleries(db, 'publication', [n.id for n in items])
    return [serialized(n, images.get(str(n.id))) for n in items]


@router.post('/admin/publications', status_code=201, dependencies=[admin])
def create(payload: PublicationInput, db: Session = Depends(get_db)):
    item = Publication(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialized(item)


@router.put('/admin/publications/{key}', dependencies=[admin])
def update(key: UUID, payload: PublicationInput, db: Session = Depends(get_db)):
    item = db.get(Publication, key)
    if not item:
        raise HTTPException(404, 'Publicación no encontrada.')
    for field, value in payload.model_dump().items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return serialized(item)
