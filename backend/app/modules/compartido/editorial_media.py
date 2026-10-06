from datetime import datetime
from io import BytesIO
import logging
import warnings
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Publication, Evento, EditorialImage, RolUsuario
from app.auth.security import require_role, get_current_user
from app.document_storage import store_bytes, read_bytes, s3_client

router = APIRouter(tags=['imagenes'])
admin = Depends(require_role(RolUsuario.admin))
Kind = Literal['publication', 'event']
LIMIT = 8 * 1024 * 1024
logger = logging.getLogger(__name__)


def metadata(image):
    return {'id': str(image.id), 'alt': image.alt, 'url': f'/public/media/{image.id}'}


def galleries(db, kind, ids):
    column = EditorialImage.publicacion_id if kind == 'publication' else EditorialImage.evento_id
    result = {}
    if ids:
        keys = [UUID(str(key)) for key in ids]
        for image in db.scalars(select(EditorialImage).where(column.in_(keys)).order_by(EditorialImage.creado_en, EditorialImage.id)):
            result.setdefault(str(getattr(image, column.key)), []).append(metadata(image))
    return result


def parent(db, kind, key, lock=False):
    model = Publication if kind == 'publication' else Evento
    query = select(model).where(model.id == key)
    if lock:
        query = query.with_for_update()
    item = db.scalar(query)
    if not item:
        raise HTTPException(404, 'Publicación o evento no encontrado.')
    return item


def visible(item):
    now = datetime.now(ZoneInfo('America/Mexico_City'))
    if isinstance(item, Publication):
        return item.publicada and item.fecha <= now.date() and (not item.vence or item.vence >= now.date())
    return item.estatus == 'Activo' and (item.fecha > now.date() or item.fecha == now.date() and item.hora >= now.time().replace(tzinfo=None))


def normalize(content):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as source:
                if source.format not in ('JPEG', 'PNG', 'WEBP') or source.width * source.height > 25_000_000 or getattr(source, 'n_frames', 1) != 1:
                    raise ValueError()
                source.load()
                image = ImageOps.exif_transpose(source).convert('RGBA' if 'A' in source.getbands() or 'transparency' in source.info else 'RGB')
                image.thumbnail((3200, 3200))
                output = BytesIO()
                image.save(output, format='WEBP', quality=90)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, 'Selecciona una imagen válida JPG, PNG o WebP, sin animación y de hasta 25 megapíxeles.')


@router.get('/admin/media/{kind}/{key}', dependencies=[admin])
def list_images(kind: Kind, key: UUID, db: Session = Depends(get_db)):
    parent(db, kind, key)
    return galleries(db, kind, [key]).get(str(key), [])


@router.post('/admin/media/{kind}/{key}', status_code=201, dependencies=[admin])
def upload(kind: Kind, key: UUID, file: UploadFile = File(...), alt: str = Form(..., min_length=1, max_length=300), db: Session = Depends(get_db)):
    description = alt.strip()
    if not description:
        raise HTTPException(422, 'Describe la imagen para las personas que usan lectores de pantalla.')
    content = file.file.read(LIMIT + 1)
    if not content or len(content) > LIMIT:
        raise HTTPException(422, 'La imagen debe pesar como máximo 8 MB.')
    content = normalize(content)
    parent(db, kind, key, lock=True)
    column = EditorialImage.publicacion_id if kind == 'publication' else EditorialImage.evento_id
    if db.scalar(select(func.count()).select_from(EditorialImage).where(column == key)) >= 5:
        raise HTTPException(409, 'Puedes agregar hasta cinco imágenes. Retira una antes de continuar.')
    stored = store_bytes(db, content, 'image/webp', f'editorial/{kind}/{key}')
    item = EditorialImage(**{column.key: key}, alt=description, media_type='image/webp', bucket=stored['bucket'], clave_archivo=stored['key'], contenido=stored['content'])
    db.add(item)
    db.commit()
    db.refresh(item)
    return metadata(item)


def image_record(db, key):
    item = db.get(EditorialImage, key)
    if not item:
        raise HTTPException(404, 'Imagen no encontrada.')
    return item


def response(item):
    return Response(read_bytes(item.bucket, item.clave_archivo, item.contenido), media_type=item.media_type, headers={'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff'})


@router.get('/public/media/{key}')
def public_image(key: UUID, db: Session = Depends(get_db)):
    item = image_record(db, key)
    owner = parent(db, 'publication' if item.publicacion_id else 'event', item.publicacion_id or item.evento_id)
    if not visible(owner):
        raise HTTPException(404, 'Imagen no publicada.')
    return response(item)


@router.get('/portal/media/{key}')
def protected_image(key: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = image_record(db, key)
    if item.publicacion_id and user.rol != RolUsuario.admin and not visible(parent(db, 'publication', item.publicacion_id)):
        raise HTTPException(403, 'No tienes acceso a esta imagen.')
    return response(item)


@router.delete('/admin/media/{key}', dependencies=[admin])
def remove(key: UUID, db: Session = Depends(get_db)):
    item = image_record(db, key)
    bucket, storage_key = item.bucket, item.clave_archivo
    db.delete(item)
    db.commit()
    if bucket != 'postgres-local':
        try:
            s3_client().delete_object(Bucket=bucket, Key=storage_key)
        except (BotoCoreError, ClientError):
            logger.error('Could not remove retired editorial object: bucket=%s key=%s', bucket, storage_key)
    return {'removed': True}
