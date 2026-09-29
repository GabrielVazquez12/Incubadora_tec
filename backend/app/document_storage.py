"""Private storage; authorization is enforced by the portal before every read."""
from functools import lru_cache
from io import BytesIO
import logging
from uuid import uuid4

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def s3_client():
    # SDK credential chain supports profiles, temporary credentials and IAM roles.
    credentials = {}
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        credentials = dict(aws_access_key_id=settings.aws_access_key_id,
                           aws_secret_access_key=settings.aws_secret_access_key,
                           aws_session_token=settings.aws_session_token or None)
    return boto3.client("s3", region_name=settings.aws_region, **credentials,
                        config=Config(signature_version="s3v4", connect_timeout=5,
                                      read_timeout=30, retries={"mode": "standard", "total_max_attempts": 3}))


def store_bytes(db, content, media_type, namespace):
    if settings.document_storage == "local":
        return {"bucket": "postgres-local", "key": str(uuid4()), "content": content}
    if not settings.aws_s3_bucket:
        from fastapi import HTTPException
        raise HTTPException(503, "El almacenamiento de documentos no está configurado.")
    bucket = settings.aws_s3_bucket
    key = f"expedientes/{namespace}/{uuid4()}"
    # Register before sending: a timeout can occur after S3 accepted the object.
    db.info.setdefault("document_uploads", []).append((bucket, key))
    s3_client().upload_fileobj(BytesIO(content), bucket, key,
                               ExtraArgs={"ContentType": media_type, "ServerSideEncryption": "AES256"})
    return {"bucket": bucket, "key": key, "content": None}


def read_bytes(bucket, key, content=None):
    if content is not None:
        return content
    if bucket == "postgres-local":
        from fastapi import HTTPException
        raise HTTPException(404, "Este registro no tiene un archivo adjunto.")
    client = s3_client()
    try:
        response = client.get_object(Bucket=bucket, Key=key)
    except client.exceptions.NoSuchKey:
        from fastapi import HTTPException
        raise HTTPException(404, "No se encontró el archivo almacenado.")
    try:
        return response["Body"].read()
    finally:
        response["Body"].close()


@event.listens_for(Session, "after_commit")
def uploads_committed(db):
    db.info.pop("document_uploads", None)


@event.listens_for(Session, "after_rollback")
def discard_failed_uploads(db):
    for bucket, key in db.info.pop("document_uploads", []):
        try:
            s3_client().delete_object(Bucket=bucket, Key=key)
        except (BotoCoreError, ClientError):
            # Do not mask the original error; operations can reconcile these keys.
            logger.error("Could not remove uncommitted document: bucket=%s key=%s", bucket, key)
