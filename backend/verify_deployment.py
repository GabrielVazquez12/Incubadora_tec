"""One-off cloud smoke test: verified DB TLS and private S3 round-trip."""
import os
from types import SimpleNamespace
from uuid import uuid4

import boto3
from sqlalchemy import text

from production_start import database_url


def main():
    os.environ["DATABASE_URL"] = database_url(os.environ)
    from app.database import engine
    from app.config import settings
    from app import document_storage as storage

    with engine.connect() as connection:
        user, ssl_enabled = connection.execute(text(
            "SELECT current_user, ssl FROM pg_stat_ssl WHERE pid = pg_backend_pid()"
        )).one()
        assert user == "incubadora_app", "Unexpected database role"
        assert ssl_enabled, "Database TLS is required"
        revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        print("RDS connection: TLS enabled; application role; migration", revision, flush=True)

    identity = boto3.client("sts", region_name=settings.aws_region).get_caller_identity()
    assert identity["Account"] == "940827433988"
    assert ":assumed-role/" in identity["Arn"], "ECS must use a task role"
    assert settings.document_storage == "s3"
    print("AWS identity:", identity["Arn"], flush=True)
    pending = SimpleNamespace(info={})
    try:
        payload = b"%PDF-1.4 cloud deployment smoke test"
        item = storage.store_bytes(pending, payload, "application/pdf", "deployment-test/" + uuid4().hex)
        assert storage.read_bytes(item["bucket"], item["key"]) == payload
        metadata = storage.s3_client().head_object(Bucket=item["bucket"], Key=item["key"])
        assert metadata["ServerSideEncryption"] == "AES256"
        print("S3 upload, download and AES256 encryption: OK", flush=True)
    finally:
        for bucket, key in pending.info.get("document_uploads", []):
            response = storage.s3_client().delete_object(Bucket=bucket, Key=key)
            assert response["ResponseMetadata"]["HTTPStatusCode"] == 204
            print("Temporary S3 object deleted", flush=True)
        engine.dispose()


if __name__ == "__main__":
    main()
