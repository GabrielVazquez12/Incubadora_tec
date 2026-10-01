"""Live HTTPS acceptance test. Run through verify-aws.ps1 -PortalFlow.

Creates isolated temporary accounts and records; cleans them in finally.
S3 deletion is logical when bucket versioning is enabled.
"""
import base64
import json
import os
import secrets
from datetime import date
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from production_start import database_url

os.environ['DATABASE_URL'] = database_url(os.environ)
from app.database import SessionLocal
from app.models import Usuario, RolUsuario, Proyecto, RegistroInicial, Documento
from app.initial_registration import fields, SPEC
from app.document_storage import s3_client

BASE = os.environ['PORTAL_URL'].rstrip('/')
run_id = uuid4().hex
emails = [f'qa-{run_id}-{role}@example.com' for role in ('student', 'coordinator', 'outsider')]
password = secrets.token_urlsafe(24)
registration_id, project_id = uuid4(), uuid4()


def request(method, path, data=None, token=None, expected=200, raw=None, content_type=None):
    headers = {'Content-Type': content_type or 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = raw if raw is not None else json.dumps(data).encode() if data is not None else None
    try:
        response = urlopen(Request(BASE + '/api' + path, data=body, headers=headers, method=method), timeout=45)
    except HTTPError as error:
        response = error
    with response:
        content = response.read()
        if response.status != expected:
            raise AssertionError(f'{method} {path}: expected {expected}, received {response.status}')
        if 'application/json' in response.headers.get('Content-Type', ''):
            return json.loads(content)
        return content


try:
    request('GET', '/admin/dashboard', expected=401)
    for email in emails:
        request('POST', '/auth/registro', {'nombre': 'QA temporal ' + run_id[:8],
            'correo': email, 'password': password, 'rol': 'estudiante'}, expected=201)
    with SessionLocal() as db:
        coordinator = db.query(Usuario).filter(Usuario.correo == emails[1]).one()
        coordinator.rol = RolUsuario.admin
        db.commit()
    student, admin, outsider = [request('POST', '/auth/login', {'correo': email,
        'password': password})['access_token'] for email in emails]
    request('GET', '/admin/dashboard', token=student, expected=403)
    assert 'proyectos' in request('GET', '/admin/dashboard', token=admin)
    print('Coordinator access and student access restrictions: OK', flush=True)

    data = {'identificacion.numero_solicitantes': '1'}
    for key, field in list(fields(data)):
        if not field.get('required'):
            continue
        kind = field['type']
        data[key] = (field['options'][0] if kind == 'select' else date.today().isoformat()
            if kind == 'date' else emails[0] if kind == 'email' else '0'
            if kind == 'number' else 'Datos temporales de prueba')
    data.update({'identificacion.numero_solicitantes': '1', 'principal.discapacidad': 'No',
        'principal.cp': '25000', 'empresa.nombre': 'QA ' + run_id,
        'descripcion.problema': 'Prueba de despliegue', 'descripcion.producto': 'Servicio de prueba'})
    pdf = b'%PDF-1.4 acceptance test'
    files = {'principal.' + doc['key']: {'name': doc['key'] + '.pdf',
        'data': base64.b64encode(pdf).decode()} for doc in SPEC['documents']}
    request('PUT', f'/portal/initialRegistrations/{registration_id}',
        {'datos': data, 'archivos': files, 'estatus': 'Pendiente'}, student)
    review = f'/portal/initial-registrations/{registration_id}/review'
    request('POST', review, {'estatus': 'En revisión', 'estatus_anterior': 'Pendiente'}, student, expected=403)
    request('POST', review, {'estatus': 'En revisión', 'estatus_anterior': 'Pendiente'}, admin)
    request('POST', review, {'estatus': 'Aprobado', 'estatus_anterior': 'En revisión'}, admin)
    project = {'registro_id': str(registration_id), 'nombre': 'QA ' + run_id,
        'descripcion': 'Prueba de despliegue', 'producto_servicio': 'Servicio de prueba',
        'fecha': date.today().isoformat(), 'estatus': 'Pendiente'}
    request('PUT', f'/portal/projects/{project_id}', project, student)
    print('Initial registration, coordinator approval and project creation: OK', flush=True)

    boundary = 'qa-' + run_id
    body = (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="qa.pdf"\r\n'
        'Content-Type: application/pdf\r\n\r\n').encode() + pdf + f'\r\n--{boundary}--\r\n'.encode()
    document = request('POST', f'/portal/projects/{project_id}/documents', token=student,
        expected=201, raw=body, content_type='multipart/form-data; boundary=' + boundary)['id']
    download = f'/portal/documents/{document}/download'
    assert request('GET', download, token=admin) == pdf
    request('GET', download, token=outsider, expected=403)
    review_payload = {'estatus': 'Aprobado', 'estatus_anterior': 'Pendiente', 'observaciones': 'QA validada'}
    request('POST', f'/portal/documents/{document}/review', review_payload, student, expected=403)
    request('POST', f'/portal/documents/{document}/review', review_payload, admin)
    request('PUT', f'/portal/projects/{project_id}', {**project, 'estatus': 'En incubación',
        'comentario': 'QA validada'}, admin)
    state = request('GET', '/portal/state', token=student)['data']
    assert next(p for p in state['projects'] if p['id'] == str(project_id))['estatus'] == 'En incubación'
    assert next(d for d in state['documents'] if d['id'] == document)['estatus'] == 'Aprobado'
    print('Private document upload/download, review and student-visible status: OK', flush=True)
finally:
    objects = set()
    with SessionLocal() as db:
        for document in db.query(Documento).filter(Documento.proyecto_id == project_id):
            if document.clave_archivo.startswith(f'expedientes/projects/{project_id}/'):
                objects.add((document.bucket, document.clave_archivo))
        registration = db.get(RegistroInicial, registration_id)
        if registration:
            for item in registration.archivos.values():
                if item.get('key', '').startswith(f'expedientes/registrations/{registration_id}/'):
                    objects.add((item['bucket'], item['key']))
        # Remove only this run's data; project relationships cascade to documents/history/members.
        project = db.get(Proyecto, project_id)
        if project:
            db.delete(project)
            db.flush()
        if registration:
            db.delete(registration)
            db.flush()
        for account in db.query(Usuario).filter(Usuario.correo.in_(emails)):
            db.delete(account)
        db.commit()
    client = s3_client()
    for bucket, key in objects:
        client.delete_object(Bucket=bucket, Key=key)
    print('Temporary SQL records removed; temporary S3 objects logically deleted.', flush=True)
