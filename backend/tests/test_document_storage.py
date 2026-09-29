"""S3 contract and rollback tests without credentials or network calls."""
import base64
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch
import boto3
from botocore.response import StreamingBody
from botocore.stub import Stubber, ANY
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.config import settings
from app import document_storage as storage
from app.initial_registration import merge_files
from app.document_validation import validate_document


class DocumentStorageTest(TestCase):
    def setUp(self):
        self.client = boto3.client("s3", region_name="us-east-1", aws_access_key_id="test", aws_secret_access_key="test")
        self.stub = Stubber(self.client)
        self.stub.activate()
        self.addCleanup(self.stub.deactivate)
        patcher = patch.object(storage, "s3_client", return_value=self.client)
        patcher.start(); self.addCleanup(patcher.stop)
        for name, value in (("document_storage", "s3"), ("aws_s3_bucket", "private-documents-test")):
            setting = patch.object(settings, name, value)
            setting.start(); self.addCleanup(setting.stop)
        self.engine = create_engine("sqlite://")
        self.addCleanup(self.engine.dispose)

    def expect_upload(self):
        self.stub.add_response("put_object", {}, {"Bucket": "private-documents-test", "Key": ANY,
            "Body": ANY, "ContentType": "application/pdf", "ServerSideEncryption": "AES256"})

    def test_upload_rollback_removes_uncommitted_object(self):
        self.expect_upload()
        with Session(self.engine) as db:
            db.execute(text("SELECT 1"))
            item = storage.store_bytes(db, b"%PDF-test", "application/pdf", "projects/abc")
            self.assertIsNone(item["content"])
            self.assertTrue(item["key"].startswith("expedientes/projects/abc/"))
            self.stub.add_response("delete_object", {}, {"Bucket": item["bucket"], "Key": item["key"]})
            db.rollback()
        self.stub.assert_no_pending_responses()

    def test_commit_keeps_object_and_download_closes_body(self):
        self.expect_upload()
        with Session(self.engine) as db:
            db.execute(text("SELECT 1"))
            item = storage.store_bytes(db, b"%PDF-test", "application/pdf", "projects/abc")
            db.commit()
            self.assertNotIn("document_uploads", db.info)
        stream = BytesIO(b"%PDF-test")
        self.stub.add_response("get_object", {"Body": StreamingBody(stream, 9)}, {"Bucket": item["bucket"], "Key": item["key"]})
        self.assertEqual(storage.read_bytes(item["bucket"], item["key"]), b"%PDF-test")
        self.assertTrue(stream.closed)
        self.stub.assert_no_pending_responses()

    def test_missing_s3_key_and_missing_configuration(self):
        self.stub.add_client_error("get_object", "NoSuchKey", http_status_code=404,
                                   expected_params={"Bucket": "private-documents-test", "Key": "missing"})
        with self.assertRaises(HTTPException) as missing:
            storage.read_bytes("private-documents-test", "missing")
        self.assertEqual(missing.exception.status_code, 404)
        with patch.object(settings, "aws_s3_bucket", ""), Session(self.engine) as db:
            with self.assertRaises(HTTPException) as config:
                storage.store_bytes(db, b"test", "application/pdf", "test")
            self.assertEqual(config.exception.status_code, 503)

    def test_s3_annex_metadata_survives_validation_and_total_limit(self):
        item = {"name": "rfc.pdf", "bucket": "private-documents-test", "key": "expedientes/example", "size": 100, "tipo": "application/pdf"}
        existing = {"principal.rfc": item}
        self.assertEqual(merge_files({}, existing, {}), existing)
        with self.assertRaises(HTTPException):
            merge_files({}, {"principal.rfc": {**item, "size": 21 * 1024 * 1024}}, {})
        changed = merge_files({}, existing, {"principal.rfc": {"name": "new.pdf", "data": base64.b64encode(b"%PDF-new").decode()}})
        self.assertNotIn("key", changed["principal.rfc"])

    def test_rejects_disguised_archive_and_unsafe_filename(self):
        for name, content in (("fake.docx", b"PK fake"), ("../plan.pdf", b"%PDF-test"), ("plan.pdf\r\n", b"%PDF-test")):
            with self.assertRaises(HTTPException):
                validate_document(name, content)
