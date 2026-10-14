"""Flujos HTTP contra PostgreSQL temporal; no modifica la BD de desarrollo."""
import base64
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
import json
import os
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from app.auth.security import hash_password
from app.config import settings
from app.models import Usuario, RolUsuario


class PortalTest(unittest.TestCase):
    def test_form_security_types_errors_and_password_revocation(self):
        person = self.create_user("form_security")
        token = self.login("form_security@example.com")
        coordinator = self.login("admin@example.com")
        invalid = self.request("POST", "/auth/registro", {"nombre": "   ", "correo": "invalid", "password": "private-password-value", "rol": "estudiante"}, status=422)
        self.assertNotIn("private-password-value", json.dumps(invalid))
        self.request("POST", "/auth/registro", {"nombre": "Otro", "correo": "FORM_SECURITY@example.com", "password": "TestPass2026!", "rol": "estudiante"}, status=409)
        self.request("POST", "/portal/registrations/" + str(uuid4()) + "/attendance", {"asistio": "false"}, coordinator, status=422)
        self.request("PUT", f"/portal/users/{person['id']}", {"nombre": "Nombre actualizado", "correo": "FORM_SECURITY@example.com", "rol": "estudiante", "password": "NewPassword2026!"}, coordinator)
        self.request("GET", "/portal/state", token=token, status=401)
        self.request("POST", "/auth/login", {"correo": "form_security@example.com", "password": "TestPass2026!"}, status=401)
        fresh = self.request("POST", "/auth/login", {"correo": "form_security@example.com", "password": "NewPassword2026!"})["access_token"]
        self.request("GET", "/portal/state", token=fresh)
        from app.auth.security import create_access_token
        malformed = create_access_token({"sub": "invalid-user-id", "rol": "admin"})
        self.request("GET", "/portal/state", token=malformed, status=401)
        self.request("POST", "/auth/login", {"correo": "form_security@example.com", "password": "x" * 100000}, status=413)

    @classmethod
    def setUpClass(cls):
        cls.name = "test_portal_" + uuid4().hex
        cls.admin_engine = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
        with cls.admin_engine.connect() as connection:
            connection.execute(text(f'CREATE DATABASE "{cls.name}"'))
        cls.addClassCleanup(cls.drop_database)
        cls.url = make_url(settings.database_url).set(database=cls.name)
        cls.env = dict(os.environ, DATABASE_URL=cls.url.render_as_string(hide_password=False), DEMO_PAYMENTS_ENABLED="true", DOCUMENT_STORAGE="local")
        subprocess.run(["alembic", "upgrade", "head"], env=cls.env, check=True, capture_output=True)
        engine = create_engine(cls.url)
        with Session(engine) as db:
            db.add(Usuario(nombre="Coordinadora", correo="admin@example.com", rol=RolUsuario.admin, password_hash=hash_password("TestPass2026!")))
            db.commit()
        engine.dispose()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        cls.base = f"http://127.0.0.1:{port}"
        cls.log = tempfile.TemporaryFile(mode="w+")
        cls.server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)], env=cls.env, stdout=cls.log, stderr=cls.log)
        cls.addClassCleanup(cls.stop_server)
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            try:
                with urlopen(cls.base + "/health", timeout=1):
                    break
            except OSError:
                if cls.server.poll() is not None:
                    cls.log.seek(0)
                    raise RuntimeError(cls.log.read())
                time.sleep(0.1)
        else:
            cls.log.seek(0)
            raise RuntimeError("La API de pruebas no inició: " + cls.log.read())

    @classmethod
    def stop_server(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            cls.server.kill()
            cls.server.wait(timeout=10)
        cls.log.close()

    @classmethod
    def drop_database(cls):
        with cls.admin_engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{cls.name}" WITH (FORCE)'))
        cls.admin_engine.dispose()

    def request(self, method, path, payload=None, token=None, status=200, binary=False):
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = Request(self.base + path, data=json.dumps(payload).encode() if payload is not None else None, headers=headers, method=method)
        try:
            response = urlopen(req, timeout=20)
        except HTTPError as error:
            response = error
        if status == 200 and path.startswith("/portal/initial-registrations/") and path.endswith("/download"):
            self.assertEqual(response.headers.get_content_type(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            self.assertIn('.docx"', response.headers["Content-Disposition"])
            self.assertIn("no-store", response.headers["Cache-Control"])
        content = response.read()
        self.assertEqual(response.status, status, f"{method} {path}: {content[:1000]!r}")
        return content if binary else json.loads(content)

    def login(self, email):
        return self.request("POST", "/auth/login", {"correo": email, "password": "TestPass2026!"})["access_token"]

    def upload_document(self, project, token, content=b"%PDF-1.4 document", name="plan.pdf", replaces=None, status=201):
        boundary = "upload-" + uuid4().hex
        body = b""
        if replaces:
            body += (f'--{boundary}\r\nContent-Disposition: form-data; name="reemplaza_id"\r\n\r\n{replaces}\r\n').encode()
        body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode() + content
        body += f'\r\n--{boundary}--\r\n'.encode()
        req = Request(self.base + f"/portal/projects/{project}/documents", data=body,
                      headers={"Authorization": "Bearer " + token, "Content-Type": f"multipart/form-data; boundary={boundary}"})
        try:
            response = urlopen(req, timeout=20)
        except HTTPError as error:
            response = error
        result = response.read()
        self.assertEqual(response.status, status, result)
        return json.loads(result)

    def test_documentos_revision_correcciones_y_permisos(self):
        from app.models import Proyecto
        owner = self.create_user("documents_owner")
        self.create_user("documents_intruder")
        self.create_user("documents_external", "externo")
        token = self.login("documents_owner@example.com")
        intruder = self.login("documents_intruder@example.com")
        external = self.login("documents_external@example.com")
        coordinator = self.login("admin@example.com")
        engine = create_engine(self.url)
        with Session(engine) as db:
            project = Proyecto(nombre="Document review", usuario_id=UUID(owner["id"]))
            db.add(project); db.commit(); pid = str(project.id)
        engine.dispose()
        self.upload_document(pid, intruder, status=403)
        self.upload_document(pid, external, status=403)
        self.upload_document(pid, token, content=b"wrong content", status=422)
        self.upload_document(pid, token, content=b"PK not a Word file", name="fake.docx", status=422)
        self.upload_document(pid, token, content=b"%PDF-" + b"x" * (5 * 1024 * 1024), status=422)
        first = self.upload_document(pid, token)["id"]
        download = f"/portal/documents/{first}/download"
        self.request("GET", download, status=401)
        self.request("GET", download, token=intruder, status=403)
        self.request("GET", download, token=external, status=403)
        self.assertEqual(self.request("GET", download, token=coordinator, binary=True), b"%PDF-1.4 document")
        review = f"/portal/documents/{first}/review"
        change = {"estatus": "Correcciones solicitadas", "estatus_anterior": "Pendiente", "observaciones": "Adjunta la versión firmada."}
        self.request("POST", review, change, token, status=403)
        self.request("POST", review, {**change, "observaciones": " "}, coordinator, status=422)
        self.upload_document(pid, token, replaces=first, status=409)
        self.request("POST", review, change, coordinator)
        self.request("POST", review, change, coordinator, status=409)
        corrected = self.upload_document(pid, token, content=b"%PDF-1.4 corrected", replaces=first)["id"]
        self.upload_document(pid, token, replaces=first, status=409)
        approval = {"estatus": "Aprobado", "estatus_anterior": "Pendiente", "observaciones": "Firma verificada."}
        self.request("POST", f"/portal/documents/{corrected}/review", approval, coordinator)
        self.upload_document(pid, token, replaces=corrected, status=409)
        docs = self.request("GET", "/portal/state", token=token)["data"]["documents"]
        old = next(d for d in docs if d["id"] == first)
        new = next(d for d in docs if d["id"] == corrected)
        self.assertFalse(old["vigente"])
        self.assertEqual(new["reemplaza_id"], first)
        self.assertEqual(new["estatus"], "Aprobado")
        self.assertEqual(len(new["historial"]), 2)
        self.assertNotIn("bucket", new)
        self.assertNotIn("contenido", new)
        self.assertEqual(self.request("GET", download, token=token, binary=True), b"%PDF-1.4 document")
        self.assertEqual(self.request("GET", "/portal/state", token=intruder)["data"]["documents"], [])

    def test_innovatec_equipment_documents_states_and_referral(self):
        from app.modules.compartido.services import today
        from app.modules.compartido.mutations import INNOVATION_CATALOG
        owner = self.create_user('innova_owner')
        self.create_user('innova_intruder')
        token, intruder = self.login('innova_owner@example.com'), self.login('innova_intruder@example.com')
        coordinator = self.login('admin@example.com')
        key, team_id = str(uuid4()), str(uuid4())
        category = INNOVATION_CATALOG['certamen']['items'][0][0]
        day = today()
        call = {'anio': day.year, 'titulo': 'Convocatoria temporal', 'descripcion': 'Datos sintéticos para probar el proceso local.', 'apertura': (day - timedelta(days=1)).isoformat(), 'cierre': (day + timedelta(days=7)).isoformat(), 'categorias': [category], 'requisitos': ['Ficha de equipo'], 'aviso_privacidad': 'Aviso sintético para pruebas; no es un aviso institucional real.', 'aviso_aprobado': True, 'publicada': True}
        self.request('PUT', f'/portal/innovatec/convocatorias/{key}', call, token, status=403)
        self.request('PUT', f'/portal/innovatec/convocatorias/{key}', {**call, 'aviso_aprobado': False}, coordinator, status=422)
        self.request('PUT', f'/portal/innovatec/convocatorias/{key}', {**call, 'apertura': True}, coordinator, status=422)
        saved_call = self.request('PUT', f'/portal/innovatec/convocatorias/{key}', call, coordinator)
        self.assertEqual(self.request('GET', '/public/innovatec/convocatorias')[0]['id'], key)
        body = {'id': team_id, 'convocatoria_id': key, 'nombre': 'Proyecto InnovaTec temporal', 'equipo': 'Equipo temporal', 'descripcion': 'Propuesta de prueba con Unicode: innovación.', 'categoria': category, 'acepto_privacidad': True, 'version_convocatoria': saved_call['version'], 'integrantes': [{'nombre': 'Alumna de prueba', 'correo': 'innova_owner@example.com', 'carrera': 'Carrera de prueba', 'semestre': 4, 'tipo': 'participante'}, {'nombre': 'Docente de prueba', 'correo': 'innova_advisor@example.com', 'tipo': 'asesor'}]}
        self.request('POST', '/portal/innovatec/equipos', body, status=401)
        self.request('POST', '/portal/innovatec/equipos', {**body, 'estado': 'acreditado'}, token, status=422)
        self.request('POST', '/portal/innovatec/equipos', {**body, 'acepto_privacidad': 'false'}, token, status=422)
        self.request('POST', '/portal/innovatec/equipos', {**body, 'integrantes': [{**body['integrantes'][0], 'semestre': '4'}, body['integrantes'][1]]}, token, status=422)
        with ThreadPoolExecutor(max_workers=2) as pool:
            registered = list(pool.map(lambda _: self.request('POST', '/portal/innovatec/equipos', body, token, status=201), range(2)))
        team = registered[0]
        self.assertEqual(registered[0]['folio'], registered[1]['folio'])
        self.assertEqual(self.request('GET', '/portal/innovatec/equipos', token=token)['total'], 1)
        self.assertEqual(self.request('GET', '/portal/innovatec/equipos', token=intruder)['items'], [])
        self.request('GET', f'/portal/innovatec/equipos/{team_id}', token=intruder, status=403)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/canalizar', token=token, status=403)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/canalizar', token=coordinator, status=409)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'acreditado', 'version': team['version'], 'motivo': 'Intento de salto'}, coordinator, status=409)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'documentacion_recibida', 'version': team['version'], 'motivo': 'Recibir documentación'}, token, status=403)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'documentacion_recibida', 'version': team['version'], 'motivo': 'Recibir documentación'}, coordinator, status=422)
        proposal = self.request('GET', '/portal/state', token=token)['data']['innovation'][0]
        self.assertEqual(proposal['equipo_id'], team_id)
        self.request('PUT', f"/portal/innovation/{proposal['id']}", {**proposal, 'estatus_anterior': proposal['estatus'], 'nombre': 'Cambio que evita el expediente'}, token, status=409)
        edited_call = self.request('PUT', f'/portal/innovatec/convocatorias/{key}', {**call, 'requisitos': ['Otro requisito'], 'version': saved_call['version']}, coordinator)
        self.assertEqual(self.request('GET', f'/portal/innovatec/equipos/{team_id}', token=token)['requisitos'], ['Ficha de equipo'])
        self.request('PUT', f'/portal/innovatec/convocatorias/{key}', {**call, 'version': saved_call['version']}, coordinator, status=409)
        self.request('PUT', f'/portal/innovatec/convocatorias/{key}', {**call, 'anio': day.year + 1, 'version': edited_call['version']}, coordinator, status=409)
        edit = {**body, 'innovacion_id': team['innovacion_id'], 'version': team['version'], 'descripcion': 'Descripción corregida por su responsable.', 'integrantes': [{**body['integrantes'][0], 'semestre': 5}, {**body['integrantes'][1], 'correo': 'corrected_advisor@example.com'}]}
        self.request('PUT', f'/portal/innovatec/equipos/{team_id}', edit, intruder, status=403)
        self.request('PUT', f'/portal/innovatec/equipos/{team_id}', {**edit, 'convocatoria_id': str(uuid4())}, token, status=422)
        team = self.request('PUT', f'/portal/innovatec/equipos/{team_id}', edit, token)
        self.request('PUT', f'/portal/innovatec/equipos/{team_id}', edit, token, status=409)
        self.assertEqual(len(team['integrantes']), 2)
        self.assertEqual(team['propuesta']['descripcion'], edit['descripcion'])
        self.assertEqual(team['propuesta']['estatus'], 'En revisión')
        self.assertEqual(team['convocatoria']['version_aceptada'], saved_call['version'])

        def upload(path, actor, fields, content=b'%PDF-1.4 document', name='ficha.pdf', expected=201):
            boundary = 'innova-' + uuid4().hex
            parts = [(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n').encode() for k, v in fields.items()]
            parts.append((f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n').encode() + content + f'\r\n--{boundary}--\r\n'.encode())
            req = Request(self.base + path, data=b''.join(parts), headers={'Authorization': 'Bearer ' + actor, 'Content-Type': f'multipart/form-data; boundary={boundary}'})
            try:
                response = urlopen(req, timeout=20)
            except HTTPError as error:
                response = error
            value = response.read()
            self.assertEqual(response.status, expected, value)
            return json.loads(value)

        route = f'/portal/innovatec/equipos/{team_id}/documentos'
        upload(route, intruder, {'requisito': 'Ficha de equipo'}, expected=403)
        upload(route, token, {'requisito': 'Otro requisito'}, expected=422)
        upload(route, token, {'requisito': 'Ficha de equipo'}, content=b'not a PDF', expected=422)
        team = upload(route, token, {'requisito': 'Ficha de equipo'})
        first = team['documentos'][0]['id']
        self.request('GET', f'/portal/innovatec/documentos/{first}', token=intruder, status=403)
        self.assertEqual(self.request('GET', f'/portal/innovatec/documentos/{first}', token=token, binary=True), b'%PDF-1.4 document')
        self.assertNotIn('bucket', team['documentos'][0])
        self.assertNotIn('contenido', team['documentos'][0])
        self.request('POST', f'/portal/innovatec/documentos/{first}/revision', {'estado': 'observado', 'estado_anterior': 'recibido', 'comentarios': ' '}, coordinator, status=422)
        team = self.request('POST', f'/portal/innovatec/documentos/{first}/revision', {'estado': 'observado', 'estado_anterior': 'recibido', 'comentarios': 'Adjunta versión firmada.'}, coordinator)
        team = upload(route, token, {'requisito': 'Ficha de equipo'}, content=b'%PDF-1.4 corrected')
        self.assertEqual(len(team['documentos']), 2)
        current = next(d for d in team['documentos'] if d['vigente'])
        self.assertNotEqual(current['id'], first)
        team = self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'documentacion_recibida', 'version': team['version'], 'motivo': 'Recibidos'}, coordinator)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'etapa_local', 'version': team['version'], 'motivo': 'Admitir'}, coordinator, status=422)
        proposal = next(p for p in self.request('GET', '/portal/state', token=coordinator)['data']['innovation'] if p['equipo_id'] == team_id)
        self.request('PUT', f"/portal/innovation/{proposal['id']}", {**proposal, 'estatus_anterior': proposal['estatus'], 'estatus': 'Aprobada'}, coordinator)
        team = self.request('POST', f"/portal/innovatec/documentos/{current['id']}/revision", {'estado': 'aprobado', 'estado_anterior': 'recibido', 'comentarios': 'Verificado'}, coordinator)
        stale = team['version']
        team = self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'etapa_local', 'version': team['version'], 'motivo': 'Admitido a etapa local'}, coordinator)
        self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'acreditado', 'version': stale, 'motivo': 'Resultado'}, coordinator, status=409)
        team = self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'acreditado', 'version': team['version'], 'motivo': 'Resultado de prueba'}, coordinator)
        with ThreadPoolExecutor(max_workers=2) as pool:
            referrals = list(pool.map(lambda _: self.request('POST', f'/portal/innovatec/equipos/{team_id}/canalizar', token=coordinator), range(2)))
        self.assertEqual(referrals[0]['proyecto_id'], referrals[1]['proyecto_id'])
        project = next(p for p in self.request('GET', '/portal/state', token=token)['data']['projects'] if p['id'] == referrals[0]['proyecto_id'])
        self.assertEqual(project['nombre'], body['nombre'])
        self.assertEqual(project['descripcion'], edit['descripcion'])
        self.assertEqual(project['owner'], owner['id'])
        member = team['integrantes'][0]
        delivery = {'estado': 'entregado', 'estado_anterior': 'pendiente', 'fecha': day.isoformat()}
        self.request('PUT', f"/portal/innovatec/integrantes/{member['id']}/diploma", delivery, token, status=403)
        self.request('PUT', f"/portal/innovatec/integrantes/{member['id']}/diploma", {**delivery, 'fecha': (day + timedelta(days=1)).isoformat()}, coordinator, status=422)
        self.request('PUT', f"/portal/innovatec/integrantes/{member['id']}/diploma", delivery, coordinator)
        self.request('GET', f"/portal/innovatec/integrantes/{member['id']}/diploma.pdf", token=intruder, status=403)
        diploma_bytes = self.request('GET', f"/portal/innovatec/integrantes/{member['id']}/diploma.pdf", token=token, binary=True)
        self.assertTrue(diploma_bytes.startswith(b'%PDF-'))
        self.assertGreater(len(diploma_bytes), 50000)
        self.request('PUT', f"/portal/innovatec/integrantes/{member['id']}/diploma", delivery, coordinator, status=409)
        self.request('GET', '/portal/innovatec/diplomas', token=token, status=403)
        self.assertEqual(self.request('GET', '/portal/innovatec/diplomas?estado=entregado', token=coordinator)['total'], 1)
        file = upload(f'/portal/innovatec/convocatorias/{key}/archivos', coordinator, {'tipo': 'manual', 'version_manual': 'prueba-1'})
        self.assertEqual(self.request('GET', f"/public/innovatec/archivos/{file['id']}", binary=True), b'%PDF-1.4 document')
        team = self.request('GET', f'/portal/innovatec/equipos/{team_id}', token=coordinator)
        logistics = {'version': team['version'], 'etapa': 'regional', 'fecha': (day + timedelta(days=2)).isoformat(), 'sede': 'Sede temporal', 'responsables': 'Coordinación de prueba', 'transporte': 'Gestión temporal', 'hospedaje': 'Gestión temporal', 'gestiones': [{'nombre': 'Traslado', 'responsable': 'Responsable temporal', 'estado': 'pendiente'}]}
        self.request('PUT', f'/portal/innovatec/equipos/{team_id}/seguimiento', logistics, token, status=403)
        team = self.request('PUT', f'/portal/innovatec/equipos/{team_id}/seguimiento', logistics, coordinator)
        self.request('PUT', f'/portal/innovatec/equipos/{team_id}/seguimiento', logistics, coordinator, status=409)
        team = self.request('POST', f'/portal/innovatec/equipos/{team_id}/estado', {'estado': 'etapa_regional', 'version': team['version'], 'motivo': 'Continuidad regional de prueba'}, coordinator)
        self.assertEqual(team['propuesta']['etapa'], 'Regional')
        self.assertEqual(self.request('GET', '/portal/innovatec/equipos?etapa=Regional', token=token)['total'], 1)
        self.assertEqual(self.request('GET', '/portal/innovatec/equipos?etapa=Local', token=token)['total'], 0)
        self.request('GET', '/portal/innovatec/equipos?etapa=ADMIN', token=token, status=422)
        event = {'nombre': 'Plática temporal InnovaTec', 'descripcion': 'Sesión exclusiva de prueba.', 'tipo': 'Taller', 'fecha': (day + timedelta(days=5)).isoformat(), 'hora': '10:00', 'cupo': 10, 'precio': 0, 'modalidad': 'Presencial', 'estatus': 'Activo'}
        talk_id = str(uuid4())
        talk = {'evento': event, 'publico': 'alumnos', 'contenido': 'Qué es InnovaTec, beneficios y proceso.', 'sede': 'Sede temporal'}
        self.request('PUT', f'/portal/innovatec/platicas/{talk_id}', talk, token, status=403)
        saved_talk = self.request('PUT', f'/portal/innovatec/platicas/{talk_id}', talk, coordinator)
        self.assertTrue(any(p['id'] == talk_id for p in self.request('GET', '/public/innovatec/platicas')))
        registration = self.request('POST', f"/portal/events/{saved_talk['evento_id']}/register", {}, token=token)
        self.assertTrue(registration['confirmed'])
        self.assertTrue(any(r['event'] == saved_talk['evento_id'] for r in self.request('GET', '/portal/state', token=token)['data']['registrations']))
        existing_event_id = str(uuid4())
        self.request('PUT', f'/portal/events/{existing_event_id}', {**event, 'nombre': 'Evento existente para plática'}, coordinator)
        reused = self.request('PUT', f'/portal/innovatec/platicas/{uuid4()}', {**talk, 'evento_id': existing_event_id, 'evento': {**event, 'nombre': 'Evento existente para plática'}}, coordinator)
        self.assertEqual(reused['evento_id'], existing_event_id)
        self.request('PUT', f'/portal/innovatec/platicas/{uuid4()}', {**talk, 'evento_id': existing_event_id}, coordinator, status=409)

    def test_incubadora_diagnostic_attention_states_and_indicators(self):
        from app.modules.compartido.services import today
        day = today()
        owner = self.create_user('incubation_owner')
        stranger = self.create_user('incubation_stranger')
        token = self.login('incubation_owner@example.com')
        other = self.login('incubation_stranger@example.com')
        coordinator = self.login('admin@example.com')
        project_id = str(uuid4())
        project = {'nombre': 'Proyecto de diagnóstico temporal', 'descripcion': 'Validar un servicio temporal.', 'producto_servicio': 'Servicio temporal', 'fecha': day.isoformat()}
        registration_id = self.initial_form(token, project)
        self.request('PUT', f'/portal/projects/{project_id}', {**project, 'registro_id': registration_id}, token)
        root = f'/portal/incubadora/proyectos/{project_id}'
        self.request('GET', root, token=other, status=403)
        folder = self.request('GET', root, token=token)
        self.assertEqual(folder['expediente']['version'], 0)
        config = self.request('GET', '/portal/incubadora/configuracion', token=coordinator)
        settings = {'version': config['version'], 'dias_inactividad': 15, 'aviso_privacidad': 'Aviso sintético exclusivo de pruebas automatizadas, sin validez institucional.', 'aviso_aprobado': True}
        self.request('PUT', '/portal/incubadora/configuracion', settings, token, status=403)
        self.request('PUT', '/portal/incubadora/configuracion', {**settings, 'aviso_aprobado': 'false'}, coordinator, status=422)
        config = self.request('PUT', '/portal/incubadora/configuracion', settings, coordinator)
        self.request('PUT', '/portal/incubadora/configuracion', settings, coordinator, status=409)
        proposal = self.request('POST', '/portal/incubadora/catalogo/propuesta', {}, coordinator)
        repeated = self.request('POST', '/portal/incubadora/catalogo/propuesta', {}, coordinator)
        self.assertEqual(len(proposal['servicios']), 12)
        self.assertEqual(len(repeated['hitos']), 12)
        self.request('POST', '/portal/incubadora/catalogo/propuesta', {}, token, status=403)
        diagnosis_id = str(uuid4())
        diagnosis = {'version': 0, 'proyecto_id': project_id, 'telefono': '+52 844 1234567', 'tipo_usuario': 'alumno', 'carrera': 'Carrera temporal', 'semestre': 4, 'perfil': 'idea de negocio', 'etapa': 'antes de vender o formalizar', 'descripcion': 'Idea temporal con texto Unicode: café y piñón.', 'estado_actual': 'idea', 'necesidades': ['cliente / mercado / validación'], 'canal_llegada': 'InnovaTec', 'proyecto_pausado': False, 'frecuencia': 'cada 15 días', 'modalidad': 'mixta', 'acepto_privacidad': True, 'version_aviso': config['version']}
        self.request('PUT', f'/portal/incubadora/diagnosticos/{diagnosis_id}', {**diagnosis, 'semestre': '4'}, token, status=422)
        self.request('PUT', f'/portal/incubadora/diagnosticos/{diagnosis_id}', {**diagnosis, 'proyecto_pausado': 'false'}, token, status=422)
        self.request('PUT', f'/portal/incubadora/diagnosticos/{diagnosis_id}', {**diagnosis, 'estado': 'formalizado'}, token, status=422)
        self.request('PUT', f'/portal/incubadora/diagnosticos/{diagnosis_id}', diagnosis, other, status=403)
        saved = self.request('PUT', f'/portal/incubadora/diagnosticos/{diagnosis_id}', diagnosis, token)
        self.assertNotIn('texto', saved['consentimiento'])
        self.request('PUT', f'/portal/incubadora/diagnosticos/{uuid4()}', diagnosis, token, status=409)
        self.request('GET', f'/portal/incubadora/diagnosticos/{diagnosis_id}/registro.pdf', token=other, status=403)
        pdf = self.request('GET', f'/portal/incubadora/diagnosticos/{diagnosis_id}/registro.pdf', token=token, binary=True)
        self.assertTrue(pdf.startswith(b'%PDF-'))
        folder = self.request('GET', root, token=token)
        self.assertEqual(folder['expediente']['proxima_revision'], (day + timedelta(days=15)).isoformat())
        version = folder['expediente']['version']
        attention = {'version': version, 'fecha': day.isoformat(), 'tipo': 'seguimiento', 'servicio_id': proposal['servicios'][0]['id'], 'actividad': 'Validar necesidades del cliente', 'responsable_id': owner['id'], 'fecha_revision': (day + timedelta(days=7)).isoformat()}
        endpoint = root + '/atenciones/' + str(uuid4())
        self.request('POST', endpoint, attention, token, status=403)
        for field in ('actividad', 'responsable_id', 'fecha_revision'):
            self.request('POST', endpoint, {key: value for key, value in attention.items() if key != field}, coordinator, status=422)
        self.request('POST', endpoint, {**attention, 'actividad': '  '}, coordinator, status=422)
        self.request('POST', endpoint, {**attention, 'fecha_revision': '2026-02-30'}, coordinator, status=422)
        self.request('POST', endpoint, {**attention, 'responsable_id': stranger['id']}, coordinator, status=422)
        with ThreadPoolExecutor(2) as pool:
            attempts = list(pool.map(lambda _: self.request('POST', endpoint, attention, coordinator), range(2)))
        self.assertEqual(attempts[0]['id'], attempts[1]['id'])
        folder = self.request('GET', root, token=token)
        self.assertEqual(len(folder['atenciones']), 1)
        self.assertEqual(folder['expediente']['estado'], 'en_seguimiento')
        self.request('PUT', root + '/estado', {'version': folder['expediente']['version'], 'estado': 'pausado', 'motivo': 'Pausa temporal', 'fecha': day.isoformat()}, coordinator, status=409)
        hito = proposal['hitos'][0]
        progress = {'version': 0, 'estado': 'cumplido', 'fecha': day.isoformat()}
        self.request('PUT', root + f"/hitos/{hito['id']}", {**progress, 'fecha': None}, token, status=422)
        self.request('PUT', root + f"/hitos/{hito['id']}", progress, other, status=403)
        self.request('PUT', root + f"/hitos/{hito['id']}", progress, token)
        folder = self.request('GET', root, token=token)
        closing = {**attention, 'version': folder['expediente']['version'], 'tipo': 'cierre', 'actividad': 'Conservar el expediente durante la pausa'}
        self.request('POST', root + '/atenciones/' + str(uuid4()), closing, coordinator)
        folder = self.request('GET', root, token=token)
        paused = self.request('PUT', root + '/estado', {'version': folder['expediente']['version'], 'estado': 'pausado', 'motivo': 'Pausa temporal de prueba', 'fecha': day.isoformat()}, coordinator)
        inactives = self.request('GET', '/portal/incubadora/seguimientos?vista=inactivos', token=coordinator)
        self.assertTrue(any(row['proyecto_id'] == project_id for row in inactives['items']))
        self.request('POST', root + '/atenciones/' + str(uuid4()), {**attention, 'version': paused['version']}, coordinator, status=409)
        recovered = {**attention, 'version': paused['version'], 'tipo': 'recuperacion', 'actividad': 'Retomar validación del cliente'}
        self.request('POST', root + '/atenciones/' + str(uuid4()), recovered, coordinator)
        folder = self.request('GET', root, token=token)
        self.assertEqual(folder['expediente']['estado'], 'activo')
        self.request('GET', '/portal/incubadora/indicadores', token=token, status=403)
        stats = self.request('GET', '/portal/incubadora/indicadores?perfil=idea%20de%20negocio', token=coordinator)
        self.assertEqual(stats['proyectos'], 1)
        self.assertEqual(stats['diagnosticos'], 1)
        self.assertEqual(stats['actividades_completadas'], 1)
        self.request('GET', '/portal/incubadora/indicadores?desde=2026-02-02&hasta=2026-01-01', token=coordinator, status=422)
        public_id = str(uuid4())
        registration = {**diagnosis, 'proyecto_id': None, 'nombre': 'Registro simplificado temporal', 'producto_servicio': 'Servicio de prueba'}
        self.request('POST', f'/portal/incubadora/registro/{public_id}', registration, coordinator, status=403)
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(lambda _: self.request('POST', f'/portal/incubadora/registro/{public_id}', registration, token, status=201), range(2)))
        self.assertEqual(results[0]['id'], results[1]['id'])
        self.assertEqual(results[0]['proyecto_id'], public_id)
        self.assertEqual(self.request('GET', f'/portal/incubadora/proyectos/{public_id}', token=token)['proyecto']['estatus'], 'En revisión')
        self.request('POST', root + '/atenciones/' + str(uuid4()), {**attention, 'version': folder['expediente']['version'], 'fecha': (day - timedelta(days=20)).isoformat(), 'fecha_revision': (day - timedelta(days=5)).isoformat()}, coordinator)
        overdue = self.request('GET', '/portal/incubadora/seguimientos?vista=vencidos', token=coordinator)
        self.assertTrue(any(row['proyecto_id'] == project_id for row in overdue['items']))

    def test_surveys_types_duplicates_freeze_privacy_and_results(self):
        from app.modules.compartido.services import today
        day = today()
        user = self.create_user('survey_respondent')
        token = self.login('survey_respondent@example.com')
        admin = self.login('admin@example.com')
        survey_id = str(uuid4())
        qids = [str(uuid4()) for _ in range(4)]
        definitions = [
            {'id': qids[0], 'titulo': 'Opción única', 'tipo': 'seleccion_unica', 'opciones': ['A', 'B']},
            {'id': qids[1], 'titulo': 'Necesidades', 'tipo': 'multiseleccion', 'opciones': ['Mercado', 'Ventas']},
            {'id': qids[2], 'titulo': 'Valoración', 'tipo': 'escala', 'minimo': 1, 'maximo': 5},
            {'id': qids[3], 'titulo': 'Comentario opcional', 'tipo': 'texto', 'obligatoria': False},
        ]
        payload = {'titulo': 'Encuesta temporal de prueba', 'descripcion': 'Datos sintéticos, sin publicación real.', 'publico': 'alumnos', 'anonima': True, 'publicada': True, 'apertura': (day - timedelta(days=7)).isoformat(), 'cierre': (day + timedelta(days=7)).isoformat(), 'preguntas': definitions}
        self.request('PUT', f'/portal/encuestas/{survey_id}', payload, token, status=403)
        self.request('PUT', f'/portal/encuestas/{survey_id}', {**payload, 'anonima': 'false'}, admin, status=422)
        self.request('PUT', f'/portal/encuestas/{survey_id}', {**payload, 'cierre': '2026-02-30'}, admin, status=422)
        survey = self.request('PUT', f'/portal/encuestas/{survey_id}', payload, admin)
        self.request('GET', '/portal/encuestas', token=token, status=403)
        response_id = str(uuid4())
        answers = {'id': response_id, 'version_encuesta': survey['version'], 'respuestas': {qids[0]: 'A', qids[1]: ['Mercado', 'Ventas'], qids[2]: 3, qids[3]: ' café y piñón '}}
        self.request('POST', f'/public/encuestas/{survey_id}/respuestas', answers, status=409)
        with urlopen(self.base + f'/public/encuestas/{survey_id}', timeout=20) as response:
            cookie = response.headers['Set-Cookie'].split(';', 1)[0]
            self.assertIn('HttpOnly', response.headers['Set-Cookie'])
            self.assertIn('SameSite=lax', response.headers['Set-Cookie'])
            self.assertTrue(json.loads(response.read())['abierta'])
        def anonymous(body, status=201):
            req = Request(self.base + f'/public/encuestas/{survey_id}/respuestas', data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Cookie': cookie}, method='POST')
            try:
                response = urlopen(req, timeout=20)
            except HTTPError as error:
                response = error
            with response:
                data = json.loads(response.read())
                self.assertEqual(response.status, status, data)
                return data
        anonymous({**answers, 'respuestas': {**answers['respuestas'], qids[2]: '3'}}, 422)
        anonymous({**answers, 'respuestas': {**answers['respuestas'], qids[1]: ['Mercado', 'Mercado']}}, 422)
        anonymous({**answers, 'respuestas': {**answers['respuestas'], qids[0]: 'ADMIN'}}, 422)
        anonymous({**answers, 'respuestas': {qids[0]: 'A'}}, 422)
        anonymous({**answers, 'respuestas': {**answers['respuestas'], str(uuid4()): 'Ajena'}}, 422)
        with ThreadPoolExecutor(2) as pool:
            confirmations = list(pool.map(lambda _: anonymous(answers), range(2)))
        self.assertEqual(confirmations[0]['id'], confirmations[1]['id'])
        anonymous({**answers, 'id': str(uuid4())}, 409)
        self.request('GET', f'/portal/encuestas/{survey_id}/resultados', token=token, status=403)
        result = self.request('GET', f'/portal/encuestas/{survey_id}/resultados', token=admin)
        self.assertEqual(result['total'], 1)
        self.assertEqual(result['preguntas'][0]['distribucion'][0]['porcentaje'], 100)
        self.assertEqual(sum(option['porcentaje'] for option in result['preguntas'][1]['distribucion']), 200)
        self.assertEqual(result['preguntas'][3]['textos'], ['café y piñón'])
        self.assertNotIn('identidad', json.dumps(result))
        self.assertNotIn('usuario_id', json.dumps(result['respuestas']))
        changed = {**payload, 'version': survey['version'], 'preguntas': [{**definitions[0], 'titulo': 'Pregunta alterada'}, *definitions[1:]]}
        self.request('PUT', f'/portal/encuestas/{survey_id}', changed, admin, status=409)
        self.request('PUT', f'/portal/encuestas/{survey_id}', {**payload, 'version': survey['version'], 'anonima': False}, admin, status=409)
        identified_id = str(uuid4())
        config = self.request('GET', '/portal/incubadora/configuracion', token=admin)
        self.request('PUT', '/portal/incubadora/configuracion', {'version': config['version'], 'aviso_privacidad': 'Aviso sintético exclusivo de pruebas; sin validez institucional.', 'aviso_aprobado': True}, admin)
        identified = self.request('PUT', f'/portal/encuestas/{identified_id}', {**payload, 'anonima': False, 'preguntas': [{**definitions[0], 'id': str(uuid4())}]}, admin)
        identified_answers = {'id': str(uuid4()), 'version_encuesta': identified['version'], 'respuestas': {identified['preguntas'][0]['id']: 'B'}, 'acepto_privacidad': True}
        self.request('POST', f'/public/encuestas/{identified_id}/respuestas', identified_answers, status=401)
        self.request('POST', f'/public/encuestas/{identified_id}/respuestas', {**identified_answers, 'acepto_privacidad': False}, token, status=422)
        self.request('POST', f'/public/encuestas/{identified_id}/respuestas', identified_answers, token, status=201)
        self.request('POST', f'/public/encuestas/{identified_id}/respuestas', {**identified_answers, 'id': str(uuid4())}, token, status=409)
        closed = self.request('PUT', f'/portal/encuestas/{survey_id}', {**payload, 'version': survey['version'], 'cierre': (day - timedelta(days=1)).isoformat()}, admin)
        self.assertGreater(closed['version'], survey['version'])
        anonymous({**answers, 'version_encuesta': closed['version']}, 409)

    def create_user(self, alias, role="estudiante"):
        return self.request("POST", "/auth/registro", {"nombre": alias, "correo": f"{alias}@example.com", "password": "TestPass2026!", "rol": role}, status=201)

    def initial_form(self, token, project):
        from app.initial_registration import fields, SPEC
        data = {"identificacion.numero_solicitantes": "1"}
        for key, field in list(fields(data)):
            if not field.get("required"):
                continue
            kind = field["type"]
            data[key] = (field["options"][0] if kind == "select" else "2026-01-01" if kind == "date" else "test@example.com" if kind == "email" else "0" if kind == "number" else "Texto de prueba")
        data.update({"identificacion.numero_solicitantes": "1", "principal.discapacidad": "No", "principal.cp": "25000", "empresa.nombre": project["nombre"], "descripcion.problema": project["descripcion"], "descripcion.producto": project["producto_servicio"]})
        files = {"principal." + doc["key"]: {"name": doc["key"] + ".pdf", "data": base64.b64encode(b"%PDF-1.4 test").decode()} for doc in SPEC["documents"]}
        key = str(uuid4())
        payload = {"datos": data, "archivos": files, "estatus": "Borrador"}
        self.request("PUT", f"/portal/initialRegistrations/{key}", {"datos": data, "estatus": "Pendiente"}, token, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "administracion": {"control.autorizo_nombre": "Fraude"}}, token, status=403)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "administracion": {"control.bloque_1.autorizo_nombre": "Fraude"}}, token, status=403)
        self.request("PUT", f"/portal/initialRegistrations/{key}", payload, token)
        self.request("GET", f"/portal/initial-registrations/{key}/download", token=token, status=409)
        self.request("GET", f"/portal/initial-registrations/{key}/download", status=401)
        self.request("PUT", f"/portal/projects/{uuid4()}", {**project, "fecha": date.today().isoformat(), "registro_id": key}, token, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "estatus": "Pendiente", "datos": {**data, "descripcion.mercado": " "}}, token, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "estatus": "Pendiente"}, token)
        self.request("PUT", f"/portal/projects/{uuid4()}", {**project, "fecha": date.today().isoformat(), "registro_id": key}, token, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "estatus": "Aprobado"}, token, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", payload, token, status=409)
        coordinator = self.login("admin@example.com")
        review = f"/portal/initial-registrations/{key}/review"
        self.request("POST", review, {"estatus": "En revisión", "estatus_anterior": "Pendiente"}, token, status=403)
        self.request("POST", review, {"estatus": "Aprobado", "estatus_anterior": "Pendiente"}, coordinator, status=409)
        self.request("POST", review, {"estatus": "En revisión", "estatus_anterior": "Pendiente"}, coordinator)
        self.request("POST", review, {"estatus": "En revisión", "estatus_anterior": "Pendiente"}, coordinator, status=409)
        self.request("POST", review, {"estatus": "Correcciones solicitadas", "estatus_anterior": "En revisión", "observaciones": " "}, coordinator, status=422)
        self.request("POST", review, {"estatus": "Correcciones solicitadas", "estatus_anterior": "En revisión", "observaciones": "Aclara el alcance del mercado."}, coordinator)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "archivos": {}}, token)
        corrected = next(r for r in self.request("GET", "/portal/state", token=token)["data"]["initialRegistrations"] if r["id"] == key)
        self.assertEqual(corrected["estatus"], "Correcciones solicitadas")
        self.assertEqual(corrected["observaciones"], "Aclara el alcance del mercado.")
        self.request("PUT", f"/portal/initialRegistrations/{key}", {**payload, "archivos": {}, "estatus": "Pendiente"}, token)
        self.request("POST", review, {"estatus": "En revisión", "estatus_anterior": "Pendiente"}, coordinator)
        self.request("POST", review, {"estatus": "Aprobado", "estatus_anterior": "En revisión", "observaciones": "Datos y anexos verificados."}, coordinator)
        self.request("POST", review, {"estatus": "Aprobado", "estatus_anterior": "En revisión"}, coordinator, status=409)
        self.request("PUT", f"/portal/initialRegistrations/{key}", payload, token, status=409)
        block_reviews = {f"control.bloque_{block}.reviso1_nombre": f"Coordinación bloque {block}" for block in range(1, 7)}
        self.request("PUT", f"/portal/initialRegistrations/{key}", {"administracion": {"control.bloque_7.reviso1_nombre": "No existe"}}, coordinator, status=422)
        self.request("PUT", f"/portal/initialRegistrations/{key}", {"administracion": block_reviews}, coordinator)
        approved = next(r for r in self.request("GET", "/portal/state", token=token)["data"]["initialRegistrations"] if r["id"] == key)
        self.assertEqual(approved['administracion'], block_reviews)
        self.assertEqual(approved["estatus"], "Aprobado")
        self.assertEqual([h["estatus"] for h in approved["historial"]], ["Borrador", "Pendiente", "En revisión", "Correcciones solicitadas", "Pendiente", "En revisión", "Aprobado"])
        self.assertTrue(approved["historial"][-1]["usuario_id"])
        self.assertNotIn('JVBER', json.dumps(self.request("GET", "/portal/state", token=token)))
        owner_word = self.request("GET", f"/portal/initial-registrations/{key}/download", token=token, binary=True)
        admin_word = self.request("GET", f"/portal/initial-registrations/{key}/download", token=coordinator, binary=True)
        self.assertEqual(owner_word, admin_word)
        with ZipFile(BytesIO(owner_word)) as document:
            text = "".join(ET.fromstring(document.read("word/document.xml")).itertext())
            self.assertIn(project["nombre"], text)
            self.assertIn(approved["datos"]["identificacion.folio"], text)
            for value in block_reviews.values():
                self.assertEqual(text.count(value), 1)
        return key

    def test_flujo_completo_y_permisos(self):
        self.request("GET", "/portal/state", status=401)
        self.request("POST", "/auth/registro", {"nombre": "Intruso", "correo": "intruso@example.com", "password": "TestPass2026!", "rol": "admin"}, status=403)
        self.request("POST", "/auth/registro", {"nombre": "Corto", "correo": "corto@example.com", "password": "123", "rol": "estudiante"}, status=422)
        alice = self.create_user("alice")
        bob = self.create_user("bob")
        outsider = self.create_user("externo", "externo")
        admin = self.login("admin@example.com")
        a, b, ext = self.login("alice@example.com"), self.login("bob@example.com"), self.login("externo@example.com")
        managedid = str(uuid4())
        managed = {"nombre": "Cuenta administrada", "correo": "managed@example.com", "rol": "estudiante", "password": "TestPass2026!"}
        self.request("PUT", f"/portal/users/{managedid}", managed, admin)
        self.assertTrue(self.login("managed@example.com"))
        self.request("PUT", f"/portal/users/{managedid}", {**managed, "nombre": "Nombre actualizado", "password": ""}, admin)
        self.request("DELETE", f"/portal/users/{managedid}", token=admin)
        self.request("POST", "/portal/event-types", {"nombre": "Seminario"}, admin)
        self.request("POST", "/portal/event-types", {"nombre": "seminario"}, admin, status=409)
        pid = str(uuid4())
        project = {"nombre": "Proyecto de prueba", "descripcion": "Validación integral", "producto_servicio": "Aplicación para gestionar proyectos", "fecha": date.today().isoformat(), "estatus": "Completado", "progreso": 100, "owner": bob["id"], "comentario": "Intento de comentario administrativo"}
        self.request("PUT", f"/portal/projects/{pid}", project, a, status=422)
        project["registro_id"] = self.initial_form(a, project)
        self.request("GET", f"/portal/initial-registrations/{project['registro_id']}/files/principal.rfc", token=b, status=403)
        self.request("GET", f"/portal/initial-registrations/{project['registro_id']}/download", token=b, status=403)
        self.assertEqual(self.request("GET", "/portal/state", token=b)["data"]["initialRegistrations"], [])
        for field in ("nombre", "descripcion", "producto_servicio"):
            self.request("PUT", f"/portal/projects/{pid}", {**project, field: "   "}, a, status=422)
        self.assertEqual(self.request("GET", "/portal/state", token=a)["data"]["projects"], [])
        self.request("PUT", f"/portal/projects/{pid}", project, a)
        snapshot = self.request("GET", "/portal/state", token=a)
        saved = snapshot["data"]["projects"][0]
        self.assertEqual(saved["owner"], alice["id"])
        self.assertEqual(saved["progreso"], 0)
        self.assertEqual(saved["estatus"], "Pendiente")
        self.assertEqual(saved["comentario"], "")
        self.assertEqual(self.request("GET", "/portal/state", token=b)["data"]["projects"], [])
        self.request("PUT", f"/portal/projects/{pid}", project, b, status=403)
        self.request("PUT", f"/portal/projects/{uuid4()}", project, ext, status=403)
        self.request("PUT", f"/portal/milestones/{uuid4()}", {"project": pid, "hito": "Prototipo", "notas": "Prueba", "fecha": project["fecha"], "progreso": 35}, b, status=403)
        self.request("POST", f"/portal/projects/{pid}/members", {"correo": "bob@example.com"}, a)
        self.assertEqual(len(self.request("GET", "/portal/state", token=b)["data"]["projects"]), 1)
        self.request("PUT", f"/portal/projects/{pid}", project, b, status=403)
        self.request("PUT", f"/portal/milestones/{uuid4()}", {"project": pid, "hito": "Prototipo", "notas": "Prueba funcional", "fecha": project["fecha"], "progreso": 35}, b)
        taskid = str(uuid4())
        task = {"project": pid, "nombre": "Preparar pitch", "estatus": "Pendiente", "fecha": project["fecha"]}
        self.request("PUT", f"/portal/tasks/{taskid}", task, a)
        self.request("PUT", f"/portal/tasks/{taskid}", {**task, "estatus": "Completado"}, b)
        pdf = b"%PDF-1.4\narchivo de prueba\n%%EOF"
        self.request("PUT", f"/portal/projects/{pid}", {**project, "file": {"name": "canvas.pdf", "data": "data:application/pdf;base64," + base64.b64encode(pdf).decode()}}, a)
        snapshot = self.request("GET", "/portal/state", token=a)
        doc = snapshot["data"]["projects"][0]["file"]
        self.assertEqual(self.request("GET", f"/portal/documents/{doc['id']}/download", token=b, binary=True), pdf)
        self.request("GET", f"/portal/documents/{doc['id']}/download", token=ext, status=403)
        self.request("PUT", f"/portal/projects/{pid}", {**project, "file": {"name": "bad.pdf", "data": "not-a-file"}}, a, status=400)
        self.request("PUT", f"/portal/projects/{pid}", {**saved, "estatus": "En incubación", "progreso": 60, "comentario": "Revisado", "siguiente_paso": "Presentar prototipo", "file": doc}, admin)
        snapshot = self.request("GET", "/portal/state", token=a)["data"]
        self.assertEqual(snapshot["projects"][0]["estatus"], "En incubación")
        self.assertEqual(snapshot["projects"][0]["comentario"], "Revisado")
        self.assertEqual(len(snapshot["history"]), 2)
        self.assertEqual(len(snapshot["milestones"]), 1)
        self.assertEqual(snapshot["tasks"][0]["estatus"], "Completado")

        future = (date.today() + timedelta(days=3)).isoformat()
        eventid = str(uuid4())
        event = {"nombre": "Taller", "descripcion": "Taller de prueba", "tipo": "Taller", "fecha": future, "hora": "10:00", "cupo": 1, "precio": 0, "modalidad": "Presencial", "estatus": "Activo"}
        self.request("PUT", f"/portal/events/{eventid}", event, a, status=403)
        self.request("PUT", f"/portal/events/{eventid}", {**event, "cupo": -1}, admin, status=422)
        self.request("PUT", f"/portal/events/{eventid}", event, admin)

        # Dos solicitudes simultáneas compiten por el último lugar.
        def reserve(token):
            req = Request(self.base + f"/portal/events/{eventid}/register", data=b'{}', headers={"Content-Type": "application/json", "Authorization": "Bearer " + token}, method="POST")
            try:
                with urlopen(req) as response:
                    return response.status
            except HTTPError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, [a, b]))
        self.assertEqual(sorted(results), [200, 409])
        regs = self.request("GET", "/portal/state", token=admin)["data"]["registrations"]
        self.assertEqual(len(regs), 1)
        self.request("DELETE", f"/portal/registrations/{regs[0]['id']}", token=ext, status=403)
        self.request("DELETE", f"/portal/registrations/{regs[0]['id']}", token=admin)
        self.request("PUT", f"/portal/events/{eventid}", {**event, "precio": 350}, admin)
        self.request("POST", f"/portal/events/{eventid}/register", {}, a, status=400)
        rejected = self.request("POST", f"/portal/events/{eventid}/register", {"resultado": "Rechazado"}, a)
        self.assertFalse(rejected["confirmed"])
        self.assertTrue(self.request("POST", f"/portal/events/{eventid}/register", {"resultado": "Pagado", "importe": 1}, a)["confirmed"])
        payments = self.request("GET", "/portal/state", token=a)["data"]["payments"]
        self.assertEqual(next(p for p in payments if p["estatus"] == "Pagado")["importe"], 350)
        self.assertEqual(self.request("GET", "/portal/state", token=b)["data"]["payments"], [])
        reg = self.request("GET", "/portal/state", token=a)["data"]["registrations"][0]
        self.request("DELETE", f"/portal/registrations/{reg['id']}", token=a)
        self.assertIn("Reembolsado", [p["estatus"] for p in self.request("GET", "/portal/state", token=a)["data"]["payments"]])

        slotid = str(uuid4())
        slot = {"fecha": future, "inicio": "09:00", "fin": "10:00"}
        self.request("PUT", f"/portal/slots/{slotid}", slot, admin)
        self.request("PUT", f"/portal/slots/{uuid4()}", slot, admin, status=409)
        appointment = str(uuid4())
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": slotid}, a)
        coordinatorid = str(uuid4())
        self.request("PUT", f"/portal/users/{coordinatorid}", {"nombre": "Otra coordinadora", "correo": "coordinator2@example.com", "rol": "admin", "password": "TestPass2026!"}, admin)
        coordinator2 = self.login("coordinator2@example.com")
        slot2 = str(uuid4())
        self.request("PUT", f"/portal/slots/{slot2}", slot, coordinator2)
        self.request("PUT", f"/portal/appointments/{uuid4()}", {"slot": slot2}, a, status=409)
        self.request("PUT", f"/portal/appointments/{uuid4()}", {"slot": slotid}, b, status=409)
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": slotid, "estatus": "Completado"}, a, status=403)
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": slotid, "estatus": "Completado"}, admin)
        self.request("DELETE", f"/portal/slots/{slotid}", token=admin, status=409)

        requestid = str(uuid4())
        application = {"nombre": "Idea externa", "descripcion": "Nueva propuesta", "producto_servicio": "Servicio de asesoría", "especialidad": "Sistemas", "telefono": "8441234567"}
        application["registro_id"] = self.initial_form(ext, application)
        self.request("PUT", f"/portal/requests/{requestid}", {**application, "producto_servicio": " "}, ext, status=422)
        self.request("PUT", f"/portal/requests/{requestid}", {**application, "telefono": "", "especialidad": ""}, ext)
        self.request("PUT", f"/portal/requests/{requestid}", {**application, "estatus": "Aprobada"}, admin)
        linked = self.request("GET", "/portal/state", token=ext)["data"]["projects"][0]
        self.assertEqual(linked["solicitud_id"], requestid)
        self.assertEqual(linked["producto_servicio"], application["producto_servicio"])
        self.assertEqual(linked["telefono"], "")
        upgraded = self.request("GET", "/portal/state", token=ext)
        self.assertEqual(upgraded["user"]["rol"], "estudiante")
        self.assertEqual(upgraded["data"]["projects"][0]["nombre"], "Idea externa")
        self.request("PUT", f"/portal/requests/{requestid}", {**application, "estatus": "Aprobada"}, admin, status=400)
        proposal = {"nombre": "Robot", "equipo": "Equipo", "lider": "Alice", "asesor": "Docente", "descripcion": "Robot de prueba", "modulo": "InnoBótica", "categoria": "Robots Minisumo"}
        innovationid = str(uuid4())
        self.request("PUT", f"/portal/innovation/{innovationid}", proposal, a)
        self.request("PUT", f"/portal/innovation/{innovationid}", {**proposal, "estatus": "En revisión", "estatus_anterior": "Borrador"}, a)
        self.request("PUT", f"/portal/innovation/{innovationid}", {**proposal, "estatus": "Aprobada", "etapa": "Regional", "estatus_anterior": "En revisión"}, admin)
        self.assertEqual(self.request("GET", "/portal/state", token=a)["data"]["innovation"][0]["etapa"], "Regional")
        admin_user = self.request("GET", "/portal/state", token=admin)["user"]
        self.request("PUT", f"/portal/users/{admin_user['id']}", {**admin_user, "rol": "externo"}, admin, status=400)
        self.request("DELETE", f"/portal/users/{alice['id']}", token=admin, status=409)
        self.request("PUT", f"/portal/users/{alice['id']}", {**alice, "rol": "admin"}, a, status=403)
        # Datos visibles nunca incluyen hashes ni archivos completos.
        self.assertNotIn('password_hash', json.dumps(self.request("GET", "/portal/state", token=admin)))

    def test_editorial_images_validation_visibility_and_permissions(self):
        from PIL import Image
        from datetime import datetime
        from zoneinfo import ZoneInfo
        day = datetime.now(ZoneInfo('America/Mexico_City')).date()
        coordinator = self.login('admin@example.com')
        self.create_user('image_student')
        student = self.login('image_student@example.com')
        payload = dict(titulo='Noticia con flyer', resumen='Resumen', contenido='Contenido', categoria='Noticia', fecha=day.isoformat(), vence=None, publicada=False, destacada=False)
        publication = self.request('POST', '/admin/publications', payload, coordinator, status=201)
        image_bytes = BytesIO()
        Image.new('RGB', (40, 80), 'white').save(image_bytes, 'PNG')

        def upload(kind, key, token=coordinator, content=None, alt='Flyer del taller', status=201):
            boundary = 'image-' + uuid4().hex
            body = (f'--{boundary}\r\nContent-Disposition: form-data; name="alt"\r\n\r\n{alt}\r\n'
                    f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="flyer.png"\r\nContent-Type: image/png\r\n\r\n').encode()
            body += image_bytes.getvalue() if content is None else content
            body += f'\r\n--{boundary}--\r\n'.encode()
            headers = {'Content-Type': 'multipart/form-data; boundary=' + boundary}
            if token:
                headers['Authorization'] = 'Bearer ' + token
            try:
                response = urlopen(Request(self.base + f'/admin/media/{kind}/{key}', data=body, headers=headers), timeout=30)
            except HTTPError as error:
                response = error
            with response:
                result = response.read()
                self.assertEqual(response.status, status, result)
                return json.loads(result)

        upload('publication', publication['id'], token=None, status=401)
        upload('publication', publication['id'], token=student, status=403)
        upload('publication', publication['id'], content=b'<svg>not an image</svg>', status=422)
        upload('publication', publication['id'], alt='   ', status=422)
        upload('publication', publication['id'], content=b'x' * (8 * 1024 * 1024 + 1), status=422)
        image = upload('publication', publication['id'])
        url = f"/public/media/{image['id']}"
        protected = f"/portal/media/{image['id']}"
        self.request('GET', url, status=404)
        self.request('GET', protected, status=401)
        self.request('GET', protected, token=student, status=403)
        converted = self.request('GET', protected, token=coordinator, binary=True)
        self.assertEqual(converted[8:12], b'WEBP')
        self.request('PUT', f"/admin/publications/{publication['id']}", {**payload, 'publicada': True}, coordinator)
        self.assertEqual(self.request('GET', url, binary=True), converted)
        feed = self.request('GET', '/public/newsletter')
        published = next(n for n in feed['publicaciones'] if n['id'] == publication['id'])
        self.assertEqual(published['imagenes'], [image])
        self.assertEqual(set(image), {'id', 'alt', 'url'})
        for _ in range(4):
            upload('publication', publication['id'])
        upload('publication', publication['id'], status=409)
        self.request('PUT', f"/admin/publications/{publication['id']}", payload, coordinator)
        self.request('GET', url, status=404)
        self.request('DELETE', f"/admin/media/{image['id']}", token=student, status=403)
        self.request('DELETE', f"/admin/media/{image['id']}", token=coordinator)
        self.request('GET', protected, token=coordinator, status=404)
        self.assertEqual(len(self.request('GET', f"/admin/media/publication/{publication['id']}", token=coordinator)), 4)

        event_id = str(uuid4())
        self.request('POST', '/portal/event-types', {'nombre': 'Material visual'}, coordinator)
        event = dict(nombre='Evento con flyer', descripcion='Actividad', tipo='Material visual', fecha=(day + timedelta(days=2)).isoformat(), hora='10:00', cupo=20, precio=0, modalidad='Presencial', estatus='Pendiente')
        self.request('PUT', f'/portal/events/{event_id}', event, coordinator)
        flyer = upload('event', event_id)
        self.request('GET', f"/public/media/{flyer['id']}", status=404)
        self.request('GET', f"/portal/media/{flyer['id']}", token=student, binary=True)
        self.request('PUT', f'/portal/events/{event_id}', {**event, 'estatus': 'Activo'}, coordinator)
        self.request('GET', f"/public/media/{flyer['id']}", binary=True)
        state = self.request('GET', '/portal/state', token=student)['data']
        self.assertEqual(next(e for e in state['events'] if e['id'] == event_id)['imagenes'], [flyer])
        self.request('PUT', f'/portal/events/{event_id}', {**event, 'estatus': 'Inactivo'}, coordinator)
        self.request('GET', f"/public/media/{flyer['id']}", status=404)

    def test_public_newsletter_visibility_permissions_and_agenda(self):
        from datetime import datetime
        from zoneinfo import ZoneInfo
        day = datetime.now(ZoneInfo('America/Mexico_City')).date()
        coordinator = self.login('admin@example.com')
        self.create_user('newsletter_student')
        student = self.login('newsletter_student@example.com')
        payload = dict(titulo='Noticias de prueba', resumen='Resumen', contenido='Contenido completo', categoria='Noticia', fecha=day.isoformat(), vence=None, publicada=True, destacada=True)
        self.request('GET', '/admin/publications', status=401)
        self.request('GET', '/admin/publications', token=student, status=403)
        self.request('POST', '/admin/publications', payload, student, status=403)
        publication = self.request('POST', '/admin/publications', payload, coordinator, status=201)
        key = publication['id']
        for overrides, visible in [({}, True), ({'publicada': False}, False), ({'fecha': (day + timedelta(days=1)).isoformat()}, False), ({'fecha': (day - timedelta(days=2)).isoformat(), 'vence': (day - timedelta(days=1)).isoformat()}, False), ({'vence': day.isoformat()}, True)]:
            self.request('PUT', f'/admin/publications/{key}', {**payload, **overrides}, coordinator)
            feed = self.request('GET', '/public/newsletter')
            self.assertEqual(any(n['id'] == key for n in feed['publicaciones']), visible)
        self.request('POST', '/admin/publications', {**payload, 'vence': (day - timedelta(days=1)).isoformat()}, coordinator, status=422)
        self.request('POST', '/admin/publications', {**payload, 'titulo': '   '}, coordinator, status=422)
        self.request('PUT', f'/admin/publications/{uuid4()}', payload, coordinator, status=404)
        self.request('POST', '/portal/event-types', {'nombre': 'Agenda pública'}, coordinator)
        event = dict(nombre='Evento público de prueba', descripcion='Descripción pública', tipo='Agenda pública', fecha=(day + timedelta(days=2)).isoformat(), hora='10:00', cupo=20, precio=0, modalidad='Presencial', estatus='Activo')
        event_ids = [str(uuid4()) for _ in range(3)]
        for eid, overrides in zip(event_ids, [{}, {'fecha': (day - timedelta(days=1)).isoformat()}, {'estatus': 'Inactivo'}]):
            self.request('PUT', f'/portal/events/{eid}', {**event, **overrides}, coordinator)
        feed = self.request('GET', '/public/newsletter')
        ids = [e['id'] for e in feed['eventos']]
        self.assertIn(event_ids[0], ids)
        self.assertNotIn(event_ids[1], ids)
        self.assertNotIn(event_ids[2], ids)
        self.assertNotIn('users', feed)
        self.assertNotIn('inscripciones', json.dumps(feed))

    def test_event_attendance_certificates_and_permissions(self):
        from app.models import Evento, Inscripcion
        person = self.create_user("certificate_owner", "externo")
        self.create_user("certificate_intruder")
        owner = self.login("certificate_owner@example.com")
        intruder = self.login("certificate_intruder@example.com")
        coordinator = self.login("admin@example.com")
        event_id, registration_id = str(uuid4()), str(uuid4())
        event = {"nombre": "Taller de participación", "descripcion": "Taller académico", "tipo": "Participación verificada", "fecha": (date.today() + timedelta(days=2)).isoformat(), "hora": "10:00", "cupo": 20, "precio": 0, "modalidad": "Presencial", "estatus": "Activo"}
        self.request("POST", "/portal/event-types", {"nombre": "Participación verificada"}, coordinator)
        self.request("PUT", f"/portal/events/{event_id}", event, coordinator)
        self.request("POST", f"/portal/events/{event_id}/register", {}, owner)
        rows = self.request("GET", "/portal/state", token=owner)["data"]["registrations"]
        registration_id = next(r["id"] for r in rows if r["event"] == event_id)
        attendance = f"/portal/registrations/{registration_id}/attendance"
        certificate = f"/portal/registrations/{registration_id}/certificate"
        self.request("POST", attendance, {"asistio": True}, status=401)
        self.request("POST", attendance, {"asistio": True}, owner, status=403)
        self.request("POST", attendance, {"asistio": True}, coordinator, status=409)
        self.request("GET", certificate, status=401)
        self.request("GET", certificate, token=intruder, status=403)
        self.request("GET", certificate, token=owner, status=409)
        engine = create_engine(self.url)
        with Session(engine) as db:
            db.get(Evento, UUID(event_id)).fecha = date.today() - timedelta(days=1)
            db.commit()
        engine.dispose()
        self.request("POST", attendance, {"asistio": True}, coordinator)
        pdf = self.request("GET", certificate, token=owner, binary=True)
        self.assertTrue(pdf.startswith(b"%PDF-"))
        self.assertTrue(self.request("GET", certificate, token=coordinator, binary=True).startswith(b"%PDF-"))
        self.request("DELETE", f"/portal/registrations/{registration_id}", token=owner, status=409)
        self.request("DELETE", f"/portal/registrations/{registration_id}", token=coordinator, status=409)
        state = self.request("GET", "/portal/state", token=owner)["data"]["registrations"]
        saved = next(r for r in state if r["id"] == registration_id)
        self.assertTrue(saved["asistio"])
        self.assertIsNotNone(saved["asistencia_por"])
        self.assertIsNotNone(saved["asistencia_fecha"])
        self.request("POST", attendance, {"asistio": False}, coordinator)
        self.request("GET", certificate, token=owner, status=409)
        self.request("DELETE", f"/portal/registrations/{registration_id}", token=owner)
        self.request("GET", certificate, token=owner, status=404)

    def test_innovation_review_corrections_stages_and_permissions(self):
        self.create_user("innovation_owner")
        self.create_user("innovation_intruder")
        self.create_user("innovation_external", "externo")
        owner = self.login("innovation_owner@example.com")
        intruder = self.login("innovation_intruder@example.com")
        external = self.login("innovation_external@example.com")
        coordinator = self.login("admin@example.com")
        key = str(uuid4())
        path = f"/portal/innovation/{key}"
        proposal = {"nombre": "Robot de seguimiento", "equipo": "Equipo ITS", "lider": "Líder", "asesor": "Docente", "descripcion": "Propuesta inicial", "modulo": "InnoBótica", "categoria": "Robots Minisumo"}
        self.request("PUT", path, proposal, external, status=403)
        self.request("PUT", path, proposal, coordinator, status=403)
        self.request("PUT", path, {**proposal, "estatus": "Aprobada"}, owner, status=403)
        self.request("PUT", path, proposal, owner)
        self.request("PUT", f"/portal/innovation/{uuid4()}", {**proposal, "nombre": proposal["nombre"].upper()}, owner, status=409)
        self.request("PUT", path, {**proposal, "estatus_anterior": "Borrador"}, intruder, status=403)
        self.request("PUT", path, {**proposal, "estatus": "Aprobada", "estatus_anterior": "Borrador"}, coordinator, status=409)
        self.request("PUT", path, {**proposal, "descripcion": "Versión completa", "estatus": "En revisión", "estatus_anterior": "Borrador"}, owner)
        self.request("PUT", path, {**proposal, "estatus_anterior": "Borrador"}, owner, status=409)
        self.request("PUT", path, {**proposal, "estatus_anterior": "En revisión"}, owner, status=409)
        self.request("PUT", path, {**proposal, "estatus": "Correcciones solicitadas", "estatus_anterior": "En revisión", "observaciones": " "}, coordinator, status=422)
        corrections = {**proposal, "estatus": "Correcciones solicitadas", "estatus_anterior": "En revisión", "observaciones": "Aclara el diseño."}
        self.request("PUT", path, corrections, coordinator)
        record = next(r for r in self.request("GET", "/portal/state", token=owner)["data"]["innovation"] if r["id"] == key)
        self.assertEqual(record["descripcion"], "Versión completa")
        self.assertEqual(record["observaciones"], "Aclara el diseño.")
        original_date = record["fecha"]
        self.request("PUT", path, {**proposal, "descripcion": "Diseño corregido", "estatus_anterior": "Correcciones solicitadas"}, owner)
        record = next(r for r in self.request("GET", "/portal/state", token=owner)["data"]["innovation"] if r["id"] == key)
        self.assertEqual(record["estatus"], "Correcciones solicitadas")
        self.request("PUT", path, {**record, "estatus": "En revisión", "estatus_anterior": "Correcciones solicitadas"}, owner)
        self.request("PUT", path, {**record, "estatus": "Aprobada", "etapa": "Nacional", "estatus_anterior": "En revisión"}, coordinator, status=409)
        self.request("PUT", path, {**record, "estatus": "Aprobada", "estatus_anterior": "En revisión"}, coordinator)
        self.request("PUT", path, {**record, "estatus": "Aprobada", "etapa": "Regional", "estatus_anterior": "Aprobada"}, coordinator)
        self.request("PUT", path, {**record, "estatus": "Aprobada", "etapa": "Local", "estatus_anterior": "Aprobada"}, coordinator, status=409)
        self.request("PUT", path, {**record, "estatus": "Aprobada", "etapa": "Nacional", "estatus_anterior": "Aprobada"}, coordinator)
        saved = next(r for r in self.request("GET", "/portal/state", token=owner)["data"]["innovation"] if r["id"] == key)
        self.assertEqual(saved["etapa"], "Nacional")
        self.assertEqual(saved["descripcion"], "Diseño corregido")
        self.assertEqual(saved["fecha"], original_date)
        self.assertEqual(len(saved["historial"]), 7)
        self.assertEqual(self.request("GET", "/portal/state", token=intruder)["data"]["innovation"], [])
        rejected = str(uuid4())
        self.request("PUT", f"/portal/innovation/{rejected}", {**proposal, "nombre": "Otra propuesta", "estatus": "En revisión"}, owner)
        rejection = {**proposal, "nombre": "Otra propuesta", "estatus": "Rechazada", "estatus_anterior": "En revisión", "observaciones": "Fuera de convocatoria."}
        self.request("PUT", f"/portal/innovation/{rejected}", rejection, coordinator)
        self.request("PUT", f"/portal/innovation/{rejected}", {**rejection, "estatus": "En revisión", "estatus_anterior": "Rechazada"}, owner, status=409)

    def test_z_request_corrections_and_resubmission(self):
        self.create_user("request_corrections", "externo")
        token = self.login("request_corrections@example.com")
        coordinator = self.login("admin@example.com")
        proposal = {"nombre": "Propuesta corregible", "descripcion": "Problema inicial", "producto_servicio": "Servicio inicial"}
        form_id = self.initial_form(token, proposal)
        proposal["registro_id"] = form_id
        request_id = str(uuid4())
        path = f"/portal/requests/{request_id}"
        self.request("PUT", path, proposal, token)
        self.request("PUT", path, {**proposal, "estatus": "Rechazada"}, coordinator, status=422)
        self.request("PUT", path, {**proposal, "estatus": "Rechazada", "observaciones": "Explica el producto corregido."}, coordinator)
        state = self.request("GET", "/portal/state", token=token)["data"]
        source = next(r for r in state["initialRegistrations"] if r["id"] == form_id)
        self.assertEqual(source["estatus"], "Correcciones solicitadas")
        self.assertEqual(source["observaciones"], "Explica el producto corregido.")
        self.assertEqual(source["historial"][-1]["anterior"], "Aprobado")
        self.request("PUT", path, proposal, token, status=422)
        self.request("GET", f"/portal/initial-registrations/{form_id}/download", token=token, status=409)
        corrected = {**source["datos"], "descripcion.producto": "Producto corregido"}
        self.request("PUT", f"/portal/initialRegistrations/{form_id}", {"datos": corrected, "estatus": "Pendiente"}, token)
        review = f"/portal/initial-registrations/{form_id}/review"
        self.request("POST", review, {"estatus": "En revisión", "estatus_anterior": "Pendiente"}, coordinator)
        self.request("POST", review, {"estatus": "Aprobado", "estatus_anterior": "En revisión"}, coordinator)
        self.request("PUT", path, proposal, token)
        self.request("PUT", path, {**proposal, "estatus": "Aprobada"}, coordinator)
        state = self.request("GET", "/portal/state", token=token)
        self.assertEqual(state["user"]["rol"], "estudiante")
        projects = [p for p in state["data"]["projects"] if p["solicitud_id"] == request_id]
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["producto_servicio"], "Producto corregido")

    def test_z_module_boundaries(self):
        """Two coordinators, cancellations and historical records stay consistent."""
        from app.models import Horario, Evento
        from app.modules.compartido.services import today
        from datetime import time as clock_time
        coordinator = self.login("admin@example.com")
        student = self.create_user("module_student")
        token = self.login("module_student@example.com")
        second_id = str(uuid4())
        self.request("PUT", f"/portal/users/{second_id}", {
            "nombre": "Coordinación módulos", "correo": "modules_admin@example.com",
            "rol": "admin", "password": "TestPass2026!"}, coordinator)
        second = self.login("modules_admin@example.com")
        future = (today() + timedelta(days=20)).isoformat()
        slot = {"fecha": future, "inicio": "10:00", "fin": "11:00"}
        first_id, other_id = str(uuid4()), str(uuid4())
        self.request("PUT", f"/portal/slots/{first_id}", slot, coordinator)
        self.request("PUT", f"/portal/slots/{other_id}", slot, second)
        self.request("PUT", f"/portal/slots/{first_id}", slot, second, status=403)
        self.request("DELETE", f"/portal/slots/{first_id}", token=second, status=403)
        appointment = str(uuid4())
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": first_id}, token)
        self.request("PUT", f"/portal/appointments/{uuid4()}", {"slot": other_id}, token, status=409)
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": first_id, "estatus": "Cancelada"}, token)
        replacement = str(uuid4())
        self.request("PUT", f"/portal/appointments/{replacement}", {"slot": first_id}, token)
        self.request("PUT", f"/portal/appointments/{appointment}", {"slot": first_id}, token, status=400)
        self.request("PUT", f"/portal/appointments/{replacement}", {"slot": first_id, "estatus": "Completado"}, coordinator)
        # A client cannot rewrite ownership, even when it supplies a forged user.
        appointments = self.request("GET", "/portal/state", token=token)["data"]["appointments"]
        self.assertEqual({a["user"] for a in appointments}, {student["id"]})
        # Historical availability may predate the new validation; booking still checks the clock.
        past_slot, past_event = uuid4(), uuid4()
        engine = create_engine(self.url)
        with Session(engine) as db:
            db.add(Horario(id=past_slot, coordinador=UUID(second_id), fecha=today(), inicio=clock_time(0), fin=clock_time(0, 1)))
            db.add(Evento(id=past_event, nombre="Evento vencido", descripcion="Prueba", tipo="Taller", fecha=today(), hora=clock_time(0), cupo=5, precio=0, modalidad="Presencial", estatus="Activo"))
            db.commit()
        engine.dispose()
        self.request("PUT", f"/portal/appointments/{uuid4()}", {"slot": str(past_slot)}, token, status=400)
        self.request("POST", f"/portal/events/{past_event}/register", {}, token, status=400)
        self.request("PUT", f"/portal/slots/{uuid4()}", {"fecha": today().isoformat(), "inicio": "00:00", "fin": "00:01"}, second, status=400)
        pending = str(uuid4())
        self.request("PUT", f"/portal/appointments/{pending}", {"slot": other_id}, token)
        demotion = {"nombre": "Coordinación módulos", "correo": "modules_admin@example.com", "rol": "estudiante"}
        self.request("PUT", f"/portal/users/{second_id}", demotion, coordinator, status=409)
        self.request("PUT", f"/portal/appointments/{pending}", {"slot": other_id, "estatus": "Cancelada"}, token)
        self.request("PUT", f"/portal/users/{second_id}", demotion, coordinator)
        self.request("PUT", f"/portal/appointments/{uuid4()}", {"slot": other_id}, token, status=409)
        # An account with only a saved draft must retain that draft and its identity.
        applicant = self.create_user("module_draft", "externo")
        external = self.login("module_draft@example.com")
        self.request("PUT", f"/portal/initialRegistrations/{uuid4()}", {"datos": {"identificacion.numero_solicitantes": "1"}, "estatus": "Borrador"}, external)
        self.request("DELETE", f"/portal/users/{applicant['id']}", token=coordinator, status=409)
        self.assertTrue(self.login("module_draft@example.com"))

    def test_folios_globales_fecha_y_guardado_simultaneo(self):
        from app.models import RegistroInicial
        from app.modules.compartido.services import today

        self.create_user("folio_estudiante")
        self.create_user("folio_externo", "externo")
        student_token = self.login("folio_estudiante@example.com")
        external_token = self.login("folio_externo@example.com")
        coordinator = self.login("admin@example.com")
        snapshot = lambda token: self.request("GET", "/portal/state", token=token)["data"]["initialRegistrations"]
        key = str(uuid4())
        forged = {"datos": {"identificacion.numero_solicitantes": "1", "identificacion.folio": "999999999", "identificacion.fecha": "1900-01-01"}}
        before_date = today().isoformat()
        self.request("PUT", f"/portal/initialRegistrations/{key}", forged, student_token)
        first = next(row for row in snapshot(student_token) if row["id"] == key)
        self.assertRegex(first["datos"]["identificacion.folio"], r"^[0-9]{6,}$")
        self.assertNotEqual(first["datos"]["identificacion.folio"], "999999999")
        self.assertIn(first["datos"]["identificacion.fecha"], [before_date, today().isoformat()])

        # Simula un folio histórico con prefijo y una fecha anterior.
        # El siguiente folio debe continuar el máximo global, no contar registros.
        historical_number = int(first["datos"]["identificacion.folio"]) + 100
        engine = create_engine(self.url)
        try:
            with Session(engine) as db:
                row = db.get(RegistroInicial, UUID(key))
                row.datos = {**row.datos, "identificacion.folio": f"ITS-{historical_number:06d}", "identificacion.fecha": "2025-02-03"}
                db.commit()
        finally:
            engine.dispose()
        for token in (student_token, coordinator):
            self.request("PUT", f"/portal/initialRegistrations/{key}", forged, token)
            kept = next(row for row in snapshot(student_token) if row["id"] == key)
            self.assertEqual(kept["datos"]["identificacion.folio"], f"ITS-{historical_number:06d}")
            self.assertEqual(kept["datos"]["identificacion.fecha"], "2025-02-03")

        # Un guardado rechazado revierte la reserva y no consume el consecutivo.
        self.request("PUT", f"/portal/initialRegistrations/{uuid4()}", {"datos": {"desconocido": "x"}}, external_token, status=422)
        ids = [str(uuid4()) for _ in range(4)]
        def save_draft(pair):
            index, record_id = pair
            token = student_token if index % 2 == 0 else external_token
            return self.request("PUT", f"/portal/initialRegistrations/{record_id}", {"datos": {"identificacion.numero_solicitantes": "1"}}, token)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(save_draft, enumerate(ids)))
        created = [row for row in snapshot(coordinator) if row["id"] in ids]
        self.assertEqual(len(created), 4)
        self.assertEqual(sorted(int(row["datos"]["identificacion.folio"]) for row in created), list(range(historical_number + 1, historical_number + 5)))
        self.assertTrue(all(row["datos"]["identificacion.fecha"] in (before_date, today().isoformat()) for row in created))
        # Reintentar un mismo borrador mantiene el folio.
        saved = next(row for row in created if row["id"] == ids[0])
        self.request("PUT", f"/portal/initialRegistrations/{ids[0]}", forged, student_token)
        retried = next(row for row in snapshot(student_token) if row["id"] == ids[0])
        self.assertEqual(retried["datos"]["identificacion.folio"], saved["datos"]["identificacion.folio"])
