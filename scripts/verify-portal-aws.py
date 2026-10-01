"""Live HTTPS acceptance test. Run through verify-aws.ps1 -PortalFlow.

Creates isolated temporary accounts and records; cleans them in finally.
S3 deletion is logical when bucket versioning is enabled.
"""
import base64
import json
import os
import secrets
from datetime import date, timedelta
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

from production_start import database_url

os.environ['DATABASE_URL'] = database_url(os.environ)
from app.database import SessionLocal
from app.models import Usuario, RolUsuario, Proyecto, RegistroInicial, Documento, Evento, Inscripcion, Pago, Horario, Tutoria, Solicitud
from app.initial_registration import fields, SPEC
from app.document_storage import s3_client

BASE = os.environ['PORTAL_URL'].rstrip('/')
run_id = uuid4().hex
emails = [f'qa-{run_id}-{role}@example.com' for role in ('student', 'coordinator', 'outsider', 'external')]
password = secrets.token_urlsafe(24)
registration_id, project_id = uuid4(), uuid4()
event_id, slot_id = uuid4(), uuid4()
external_registration_id, request_id = uuid4(), uuid4()


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
            'correo': email, 'password': password, 'rol': 'externo' if email == emails[3] else 'estudiante'}, expected=201)
    with SessionLocal() as db:
        coordinator = db.query(Usuario).filter(Usuario.correo == emails[1]).one()
        coordinator.rol = RolUsuario.admin
        db.commit()
    student, admin, outsider, external = [request('POST', '/auth/login', {'correo': email,
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
    milestone_id, task_id = uuid4(), uuid4()
    request('PUT', f'/portal/milestones/{milestone_id}', {'project': str(project_id),
        'hito': 'QA avance', 'notas': 'Validación temporal', 'fecha': date.today().isoformat(), 'progreso': 35}, student)
    task = {'project': str(project_id), 'nombre': 'QA tarea', 'fecha': date.today().isoformat(), 'estatus': 'Pendiente'}
    request('PUT', f'/portal/tasks/{task_id}', task, admin)
    request('PUT', f'/portal/tasks/{task_id}', {**task, 'estatus': 'Completado'}, student)
    request('PUT', f'/portal/tasks/{task_id}', task, outsider, expected=403)
    state = request('GET', '/portal/state', token=admin)['data']
    assert next(p for p in state['projects'] if p['id'] == str(project_id))['progreso'] == 35
    assert next(t for t in state['tasks'] if t['id'] == str(task_id))['estatus'] == 'Completado'
    print('Project milestones, tasks and coordinator report data: OK', flush=True)

    future = (date.today() + timedelta(days=30)).isoformat()
    event = {'nombre': 'QA temporal ' + run_id, 'descripcion': 'Verificación automática; no inscribirse',
        'tipo': state['eventTypes'][0], 'fecha': future, 'hora': '10:00', 'cupo': 1,
        'precio': 0, 'modalidad': 'En línea', 'estatus': 'Activo'}
    request('PUT', f'/portal/events/{event_id}', event, admin)
    assert request('POST', f'/portal/events/{event_id}/register', {}, student)['confirmed']
    request('POST', f'/portal/events/{event_id}/register', {}, outsider, expected=409)
    registration = next(r for r in request('GET', '/portal/state', token=student)['data']['registrations'] if r['event'] == str(event_id))
    request('DELETE', f"/portal/registrations/{registration['id']}", token=outsider, expected=403)
    request('DELETE', f"/portal/registrations/{registration['id']}", token=student)
    request('PUT', f'/portal/events/{event_id}', {**event, 'precio': 100}, admin)
    request('POST', f'/portal/events/{event_id}/register', {'resultado': 'Pagado'}, student, expected=409)
    assert not any(p['event'] == str(event_id) for p in request('GET', '/portal/state', token=student)['data']['payments'])
    print('Free events, capacity, cancellation and disabled real payments: OK', flush=True)

    request('PUT', f'/portal/slots/{slot_id}', {'fecha': future, 'inicio': '10:00', 'fin': '11:00'}, admin)
    appointment_id = uuid4()
    request('PUT', f'/portal/appointments/{appointment_id}', {'slot': str(slot_id)}, student)
    request('PUT', f'/portal/appointments/{uuid4()}', {'slot': str(slot_id)}, outsider, expected=409)
    request('PUT', f'/portal/appointments/{appointment_id}', {'slot': str(slot_id), 'estatus': 'Completado'}, student, expected=403)
    request('PUT', f'/portal/appointments/{appointment_id}', {'slot': str(slot_id), 'estatus': 'Completado'}, admin)
    request('DELETE', f'/portal/slots/{slot_id}', token=admin, expected=409)
    print('Availability, exclusive booking, completion and tutoring history: OK', flush=True)

    external_data = {**data, 'empresa.nombre': 'QA solicitud ' + run_id, 'principal.correo1': emails[3]}
    request('PUT', f'/portal/initialRegistrations/{external_registration_id}',
        {'datos': external_data, 'archivos': files, 'estatus': 'Pendiente'}, external)
    review = f'/portal/initial-registrations/{external_registration_id}/review'
    for status, previous in [('En revisión', 'Pendiente'), ('Aprobado', 'En revisión')]:
        request('POST', review, {'estatus': status, 'estatus_anterior': previous}, admin)
    proposal = {**project, 'registro_id': str(external_registration_id), 'estatus': 'En revisión'}
    proposal_path = f'/portal/requests/{request_id}'
    request('PUT', proposal_path, proposal, external)
    request('PUT', proposal_path, {**proposal, 'estatus': 'Rechazada', 'observaciones': 'QA: corregir producto'}, admin)
    external_state = request('GET', '/portal/state', token=external)['data']
    source = next(r for r in external_state['initialRegistrations'] if r['id'] == str(external_registration_id))
    assert source['estatus'] == 'Correcciones solicitadas'
    assert source['observaciones'] == 'QA: corregir producto'
    request('PUT', proposal_path, proposal, external, expected=422)
    request('PUT', f'/portal/initialRegistrations/{external_registration_id}',
        {'datos': {**source['datos'], 'descripcion.producto': 'QA producto corregido'}, 'estatus': 'Pendiente'}, external)
    for status, previous in [('En revisión', 'Pendiente'), ('Aprobado', 'En revisión')]:
        request('POST', review, {'estatus': status, 'estatus_anterior': previous}, admin)
    request('PUT', proposal_path, proposal, external)
    request('PUT', proposal_path, {**proposal, 'estatus': 'Aprobada'}, admin)
    external_state = request('GET', '/portal/state', token=external)
    assert external_state['user']['rol'] == 'estudiante'
    linked = next(p for p in external_state['data']['projects'] if p['solicitud_id'] == str(request_id))
    assert linked['producto_servicio'] == 'QA producto corregido'
    print('External request rejection, correction, resubmission and admission: OK', flush=True)
finally:
    objects = set()
    with SessionLocal() as db:
        db.query(Tutoria).filter(Tutoria.slot == slot_id).delete(synchronize_session=False)
        db.query(Horario).filter(Horario.id == slot_id).delete(synchronize_session=False)
        db.query(Inscripcion).filter(Inscripcion.event == event_id).delete(synchronize_session=False)
        db.query(Pago).filter(Pago.event == event_id).delete(synchronize_session=False)
        db.query(Evento).filter(Evento.id == event_id).delete(synchronize_session=False)
        for document in db.query(Documento).filter(Documento.proyecto_id == project_id):
            if document.clave_archivo.startswith(f'expedientes/projects/{project_id}/'):
                objects.add((document.bucket, document.clave_archivo))
        registrations = db.query(RegistroInicial).filter(RegistroInicial.id.in_([registration_id, external_registration_id])).all()
        for registration in registrations:
            for item in registration.archivos.values():
                if item.get('key', '').startswith(f'expedientes/registrations/{registration.id}/'):
                    objects.add((item['bucket'], item['key']))
        # Remove only this run's data; project relationships cascade to documents/history/members.
        project = db.get(Proyecto, project_id)
        if project:
            db.delete(project)
            db.flush()
        for external_project in db.query(Proyecto).filter(Proyecto.solicitud_id == request_id):
            db.delete(external_project)
        db.flush()
        db.query(Solicitud).filter(Solicitud.id == request_id).delete(synchronize_session=False)
        for registration in registrations:
            db.delete(registration)
            db.flush()
        for account in db.query(Usuario).filter(Usuario.correo.in_(emails)):
            db.delete(account)
        db.commit()
    client = s3_client()
    for bucket, key in objects:
        client.delete_object(Bucket=bucket, Key=key)
    print('Temporary SQL records removed; temporary S3 objects logically deleted.', flush=True)
