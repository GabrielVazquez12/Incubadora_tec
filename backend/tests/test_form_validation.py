"""Critical validation regressions without external credentials."""
import base64
from datetime import date
from io import BytesIO
import unittest
from zipfile import ZipFile, ZIP_DEFLATED
from unittest.mock import patch
import asyncio

from fastapi import HTTPException
from pydantic import ValidationError
from app.schemas.usuario import UsuarioCreate, LoginRequest
from app.schemas.portal import AttendanceInput, EventInput, ProjectInput, UserInput
from app.modules.compartido.newsletter import PublicationInput
from app.initial_registration import validate_data, merge_files
from app.document_validation import validate_document


class FormValidationTest(unittest.TestCase):
    def test_login_throttle_expires_and_does_not_store_plain_email(self):
        from app.auth import rate_limit
        with patch.dict(rate_limit._attempts, {}, clear=True), patch.object(rate_limit, "monotonic", return_value=100) as clock:
            for _ in range(rate_limit.LIMIT):
                rate_limit.login_attempt("limited@example.com")
            with self.assertRaises(HTTPException) as error:
                rate_limit.login_attempt("limited@example.com")
            self.assertEqual(error.exception.status_code, 429)
            self.assertNotIn("limited@example.com", rate_limit._attempts)
            clock.return_value = 100 + rate_limit.WINDOW
            rate_limit.login_attempt("limited@example.com")

    def test_chunked_body_limits_and_unused_urlencoded_format(self):
        from app.request_safety import BodyLimitMiddleware
        async def run(headers, chunks):
            responses = []
            called = []
            async def app(scope, receive, send):
                called.append(True)
            async def receive():
                return chunks.pop(0)
            async def send(message):
                responses.append(message)
            await BodyLimitMiddleware(app)({"type": "http", "method": "POST", "path": "/auth/login", "headers": headers}, receive, send)
            self.assertFalse(called)
            return responses[0]["status"]
        self.assertEqual(asyncio.run(run([], [{"type": "http.request", "body": b"x" * 40000, "more_body": True}, {"type": "http.request", "body": b"x" * 40000, "more_body": False}])), 413)
        self.assertEqual(asyncio.run(run([(b"content-type", b"application/x-www-form-urlencoded")], [])), 415)

    def test_account_normalization_unicode_and_bcrypt_byte_limit(self):
        values = dict(nombre="  María O'Neill-Güemes  ", correo="Maria@Example.COM", password="PassWord 2026", rol="estudiante")
        user = UsuarioCreate(**values)
        self.assertEqual(user.nombre, "María O'Neill-Güemes")
        self.assertEqual(user.correo, "maria@example.com")
        for password in ("short", "á" * 37, "x" * 73):
            with self.assertRaises(ValidationError):
                UsuarioCreate(**{**values, "password": password})
        with self.assertRaises(ValidationError):
            UsuarioCreate(**{**values, "nombre": "   "})
        for invalid in ("Nombre\x00inválido", "Nombre\ud800"):
            with self.assertRaises(ValidationError):
                UsuarioCreate(**{**values, "nombre": invalid})
        with self.assertRaises(ValidationError):
            LoginRequest(correo="maria@example.com", password="á" * 37)
        self.assertEqual(UserInput(nombre="María", correo="maria@example.com", rol="estudiante", password="").password, "")

    def test_boolean_json_values_are_not_coerced(self):
        for value in ("false", "true", 0, 1, None):
            with self.assertRaises(ValidationError):
                AttendanceInput(asistio=value)
            with self.assertRaises(ValidationError):
                PublicationInput(titulo="Noticia", resumen="Resumen", contenido="Contenido", fecha="2026-10-13", publicada=value)
        self.assertFalse(AttendanceInput(asistio=False).asistio)

    def test_event_numbers_and_clock_have_explicit_types(self):
        values = dict(nombre="Taller", descripcion="Contenido", tipo="Taller", fecha="2026-10-20", hora="10:00", cupo=10, precio=0, modalidad="Presencial", estatus="Activo")
        for field, value in (("cupo", True), ("cupo", "10"), ("cupo", 10.5), ("precio", True), ("precio", "10"), ("precio", float("inf")), ("precio", 1.234), ("hora", "10:00+03:00"), ("hora", 3600), ("fecha", 0), ("fecha", "2026-02-30")):
            with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                EventInput(**{**values, field: value})
        self.assertEqual(EventInput(**values).cupo, 10)
        for value in (True, "20", 20.5, -1, 101):
            with self.assertRaises(ValidationError):
                ProjectInput(nombre="Proyecto", fecha="2026-10-13", progreso=value)

    def test_administrative_fields_use_the_actual_participant_count(self):
        clean = validate_data({"control.bloque_1.elaboro_fecha": "2026-10-13", "revision.socio_1.rfc": "Revisado"}, administrative=True, participant_data={"identificacion.numero_solicitantes": "2"})
        self.assertEqual(clean["revision.socio_1.rfc"], "Revisado")
        for values in ({"control.bloque_1.elaboro_fecha": "2026-02-30"}, {"revision.socio_2.rfc": "Revisado"}, {"empresa.nombre": "Cambio no autorizado"}):
            with self.assertRaises(HTTPException):
                validate_data(values, administrative=True, participant_data={"identificacion.numero_solicitantes": "2"})

    def test_annex_names_and_images_are_checked_by_content(self):
        for name, content in (("../personal.pdf", b"%PDF-test"), ("photo.png", b"\x89PNG\r\n\x1a\ninvalid"), ("bad\x00.pdf", b"%PDF-test")):
            with self.assertRaises(HTTPException):
                merge_files({"identificacion.numero_solicitantes": "1"}, {}, {"principal.rfc": {"name": name, "data": base64.b64encode(content).decode()}})

    def test_docx_compression_bombs_and_macros_are_rejected(self):
        for extra in ("word/vbaProject.bin", "../unsafe.xml", "word/oversized.xml"):
            output = BytesIO()
            with ZipFile(output, "w", ZIP_DEFLATED) as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr("word/document.xml", "<document/>")
                archive.writestr(extra, "x" * 1_000_000)
            with self.assertRaises(HTTPException):
                validate_document("file.docx", output.getvalue())

    def test_registration_income_precision_and_birth_date(self):
        for values in ({"principal.ingreso_personal": "1.234"}, {"principal.nacimiento": "9999-12-31"}, {"principal.ingreso_personal": "NaN"}, {"identificacion.numero_solicitantes": "1.5"}):
            with self.assertRaises(HTTPException):
                validate_data(values)
