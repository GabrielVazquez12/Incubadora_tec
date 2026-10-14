# Fase B: proceso local InnovaTec

Se extiende la propuesta existente (`Innovacion`) con un expediente de equipo; no se sustituye el módulo `/innovatecnm` ni su revisión. Se conserva el destino real del enlace InnovaTecNM, que actualmente es interno. La dirección externa institucional sigue pendiente.

## Funcionalidad

- Proceso público de once pasos, convocatoria y manual descargables, inscripción con integrantes y asesor, folio e identificación de reintentos.
- Convocatoria administrable por año, privacidad aprobada, fechas y etapas coherentes, requisitos y categorías del catálogo existente. Sin datos oficiales inventados; publicar exige configuración real.
- Expediente propio o de coordinación, edición versionada, documentos privados revisables y versiones históricas, transiciones válidas y revisión de la propuesta por el endpoint anterior.
- Logística local/regional/nacional, responsables, sede, jurado, resultados y lista de gestiones.
- Canalización idempotente a `Proyecto`, precargando nombre/descripcion y conservando vínculos e historial en ambos lados.
- Diplomas digitales de participantes y asesores, estados de generación/entrega, descarga protegida y listado CSV. No contienen firmas o sellos inventados.
- Pláticas para alumnos/docentes asociadas a `Evento`, nuevo o existente. Conservan inscripción, cupo, asistencia y constancia anteriores. El enlace al control de asistencia selecciona su evento.

## Archivos

Backend: `models/innovatec.py`, `schemas/innovatec.py`, `modules/innovacion/{routes,services}.py`, exportaciones de modelos, `main.py`, `request_safety.py`, integración de `schemas/portal.py` y `modules/compartido/{mutations,routes}.py`, generador `event_certificates.py`, copia exacta de marca en `app/assets/`.

Frontend: `modules/innovatec/{api.js,PublicInnova.jsx,CallAdmin.jsx,Teams.jsx,Talks.jsx,innovatec.css}`, `App.jsx`, integración de `Innovation.jsx`, `Projects.jsx`, `Registrations.jsx` y `EventManagement.jsx`.

Verificación: `tests/test_portal.py`, `tests/test_migraciones.py`, `frontend/scripts/innovatec-browser.cjs`, corrección de selección completa de campos en `browser-helper.cjs`, switches opcionales en `scripts/verify-design-local.ps1`. No dependencias nuevas de aplicación.

## Integridad y autorización

Migración aditiva `bc36a33dcdcb`, posterior a `3a608b5c8533`: seis tablas, llaves foráneas, índices, unicidad y CHECK. No cambia tablas existentes. Downgrade se rechaza si cualquiera de las tablas nuevas contiene datos; rollback de aplicación conserva el esquema. Antes de migrar producción se requiere backup y preflight.

El servidor valida booleanos e enteros JSON estrictos, fechas reales, semestres, correo normalizado, categorías, IDs y propiedad; rechaza propiedades extra. Congela consentimiento y requisitos aceptados. Archivos de hasta 5 MB pasan el validador de contenido existente y almacenamiento privado; respuestas de metadatos no incluyen bytes o claves de almacenamiento. La coordinación gestiona convocatoria, revisión, logística y diplomas; el emprendedor confirma su captura con cuenta y consulta únicamente sus equipos. No se añaden roles técnicos arbitrarios.

Versiones, bloqueo con orden uniforme y refresco bajo bloqueo evitan sobrescrituras y duplicados. La prueba concurrente detectó y corrigió una lectura obsoleta de SQLAlchemy durante la canalización.

## Verificación

- `npm test --prefix frontend`: aprobado; 56 pantallas y 75 enlaces, 14 destinos heredados y límites por rol. Tres advertencias heredadas de `StaticRouter` sin fallos.
- `npm run build --prefix frontend`: aprobado, 158 módulos, JS 421.05 kB (129.07 kB gzip).
- `./scripts/verify-design-local.ps1 -Port 8091 -InnovaTec`: aprobado. Chrome real: marca, cabecera y menús anteriores, formularios anteriores, convocatoria, consentimiento, integrantes, doble envío, expediente propio/coordinador y revisión anterior; móvil de 320 px y escritorio. PostgreSQL y cuentas temporales aislados, eliminados al terminar.
- `python -m unittest discover -s tests -v` dentro del contenedor con PostgreSQL aislado: 34 pruebas aprobadas en 106.453 s, sin omisiones; incluye reversión protegida y reutilización de evento.
- Diploma de prueba renderizado con Poppler y revisado visualmente: una página A4, 140591 bytes, sin recortes. Poppler solo se instaló en una imagen temporal de QA; no en producción.

## Cómo probar

1. Aplicar migraciones en desarrollo y acceder como coordinador a Gestión InnovaTec → Convocatoria. Guardar borrador, completar requisitos, categorías, fechas y aviso aprobado; publicar solo con datos institucionales válidos.
2. Abrir `/innovatec/convocatoria` y `/innovatec/inscripcion`. Confirmar con cuenta de emprendedor, participante y asesor; aceptar aviso vigente. Conservar folio.
3. Desde Proyectos → equipos InnovaTec, revisar captura y subir requisitos. Coordinación revisa documentos y propuesta; observar y corregir conserva versiones.
4. Avanzar a etapa local tras aprobar propuesta y documentación; registrar logística y resultados; acreditar y continuar regional/nacional.
5. Generar/descargar diploma y marcar entrega con fecha válida. Canalizar equipo acreditado y comprobar que el reintento devuelve el mismo proyecto.
6. Crear plática o asociar evento existente; inscribirse desde la cuenta y registrar asistencia desde el módulo Eventos anterior.

## Pendientes institucionales y siguientes fases

Convocatoria/manual oficiales, fechas/sedes, aviso aprobado, requisitos reales y dirección externa InnovaTecNM. No se publican ejemplos ni se envían correos. La integración de difusión y encuestas corresponde a E/D; la bitácora de la Incubadora, a C. Las cifras no se precargan como participación real. Asesores administrativos con permisos propios se abordan en F, conservando roles existentes.

Esta fase aún no se ha desplegado en AWS; la fase A continúa allí. El despliegue posterior debe incluir backup, migración y comprobación de salud.
