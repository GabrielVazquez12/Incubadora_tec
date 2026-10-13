# Auditoría de formularios — Incubadora_tec

Fecha: 13 de octubre de 2026. Base: `main` (`5c1243d`). Esta revisión corresponde a React/Vite, FastAPI/Pydantic 2, SQLAlchemy/Alembic y PostgreSQL; no al repositorio Express/MySQL revisado anteriormente.

## Formularios revisados

| Formulario u operación | Interfaz | API y persistencia |
| --- | --- | --- |
| Registro de cuenta | `modules/autenticacion/Registro.jsx` | `/auth/registro`, `UsuarioCreate`, `usuarios` |
| Inicio de sesión | `modules/autenticacion/Login.jsx` | `/auth/login`, bcrypt, JWT y `usuarios` |
| Crear/editar/eliminar usuarios | `modules/coordinacion/Users.jsx` | `/portal/users/{id}`, `UserInput`, `usuarios` y referencias |
| Formato completo, socios, empleos, anexos y borrador | `shared/registration/FullRegistration.jsx` | `/portal/initialRegistrations/{id}`, `InitialFormInput`, `registros_iniciales` |
| Revisión administrativa y aprobación/correcciones | `modules/coordinacion/RegistrationReview.jsx` | `/portal/initial-registrations/{id}/review`, historial JSON |
| Crear/vincular proyecto aprobado | `modules/estudiantes/ProjectForm.jsx` | `/portal/projects/{id}`, `ProjectInput`, `proyectos` |
| Seguimiento, progreso, estado y orientación | `shared/projects/Projects.jsx` | `/portal/projects/{id}`, `historial_estatus` |
| Integrantes por correo | `shared/projects/Projects.jsx` | `/portal/projects/{id}/members`, `integrantes_proyecto` |
| Avances y tareas | `shared/projects/Projects.jsx` | `/portal/milestones/{id}`, `/portal/tasks/{id}`, `avances`, `tareas` |
| Subir/corregir/revisar documentos | `shared/projects/Documents.jsx` | `/portal/projects/{id}/documents`, `/portal/documents/{id}/review`, `documentos`, S3 privado |
| Solicitud externa y aprobación/rechazo | `shared/applications/Application.jsx` | `/portal/requests/{id}`, `solicitudes`, conversión a emprendedor y proyecto |
| Crear/editar/desactivar eventos | `modules/coordinacion/EventManagement.jsx` | `/portal/events/{id}`, `EventInput`, `eventos` |
| Tipos de evento | `modules/coordinacion/EventManagement.jsx` | `/portal/event-types`, `tipos_evento` |
| Inscripción, cancelación y pago de prueba | `shared/events/{Events,Checkout,Registrations}.jsx` | `/portal/events/{id}/register`, `/portal/registrations/{id}`, `inscripciones`, `pagos` |
| Confirmación/corrección de asistencia | `modules/coordinacion/EventManagement.jsx` | `/portal/registrations/{id}/attendance`, constancia autorizada |
| Disponibilidad, reserva, cancelación y conclusión | `shared/tutoring/Tutoring.jsx` | `/portal/slots/{id}`, `/portal/appointments/{id}`, `horarios`, `tutorias` |
| Propuestas Innovatec, borrador, envío y resolución | `modules/innovacion/Innovation.jsx` | `/portal/innovation/{id}`, `Innovacion.datos` |
| Publicaciones, vigencia y checkboxes | `modules/coordinacion/Publications.jsx` | `/admin/publications`, `PublicationInput`, `publicaciones` |
| Galerías, imágenes y texto alternativo | `shared/EditorialImages.jsx` | `/admin/media/...`, `imagenes_editoriales`, S3 privado |
| Búsquedas, filtros, reportes y descargas | componentes de boletín, eventos, proyectos, usuarios y reportes | consultas autorizadas y exportación CSV; no nuevos campos persistentes |

Se inspeccionaron todos los componentes React, routers, esquemas, modelos y migraciones existentes antes de las modificaciones. Los formularios usan `api/client.js`; FastAPI recibe JSON o multipart, valida con Pydantic, aplica permisos y reglas en los handlers, y guarda con SQLAlchemy. `get_db()` revierte transacciones fallidas; S3 elimina objetos no confirmados mediante el mecanismo existente. Producción sirve React y `/api` desde el mismo origen HTTPS.

## Problemas encontrados

| Archivo | Problema y riesgo | Solución implementada |
| --- | --- | --- |
| `app/schemas/{portal,usuario}.py` | Alto: booleanos/números podían convertirse implícitamente; login no acotaba el límite bcrypt | `StrictInt`, `StrictBool`, precio JSON numérico finito con dos decimales, límite UTF-8 de 72 bytes y fechas/horas explícitas |
| `app/modules/compartido/newsletter.py` | Alto: `"false"`/`0` aceptados como booleanos | únicamente booleanos JSON reales |
| `app/main.py` | Alto: errores de validación reflejaban los valores enviados, incluyendo campos sensibles | respuesta 422 con ubicación/tipo/mensaje, sin input ni contexto; errores internos genéricos y logs sin payloads/SQL |
| `app/request_safety.py` | Alto: cuerpos JSON/multipart sin límite agregado antes del parsing | límites también para solicitudes fragmentadas: 64 KiB general, 9 MiB proyectos/imágenes, 30 MiB registro base64 |
| `app/auth/security.py` | Alto: identificador JWT inválido podía llegar a SQL; tokens seguían válidos tras cambiar contraseña | UUID validado, hash inválido tratado como credencial incorrecta, versión de autenticación verificada contra BD |
| `app/auth/rate_limit.py` | Alto: login sin restricción de intentos | 60 intentos por cuenta/15 minutos; contador acotado, llave hash, respuesta 429/Retry-After |
| `app/modules/coordinacion/mutations.py` | Alto: duplicados normalizados y cambio de contraseña/rol sin revocación | detección excluyendo la cuenta actual, incremento de `auth_version` |
| `app/modules/compartido/mutations.py` | Alto: revisión administrativa validaba longitud y llaves pero no formatos; categorías Innovatec arbitrarias | mismo validador de campos administrativos, socios reales y catálogo existente para nuevas propuestas; datos históricos preservados |
| `app/initial_registration.py` | Alto: anexos admitían nombres con rutas e imágenes con solo firma de bytes | validación del nombre, decodificación y verificación de imágenes; fechas de nacimiento futuras, precisión de ingresos y coherencia de dependientes |
| `app/document_validation.py` | Alto: DOCX sin límites de expansión/entradas | rechaza macros, rutas peligrosas, cifrado, exceso de entradas/tamaño expandido y relaciones de compresión abusivas |
| `backend/requirements.txt` | Alto: versiones vulnerables de parser multipart/JWT y spooling de uploads | FastAPI 0.116.2 / Starlette 0.48.0, python-multipart 0.0.30 y python-jose 3.5.0; se conserva Pydantic y el resto del stack |
| modelos y migración `3a608b5c8533` | Alto: algunas reglas de integridad existían solo en la aplicación | índices únicos normalizados, reserva confirmada única por horario y CHECKs de rangos/estados/fechas |
| `shared/portal/PortalContext.jsx` | Alto: escritura confirmada seguida de fallo al refrescar se comunicaba como fallo de guardado, favoreciendo reintentos | devuelve el resultado confirmado y muestra aviso de actualización pendiente |
| `shared/portal/ui.jsx` y formularios | Medio: estados de envío incompletos, espacios como valores required, límites incongruentes | componente Form con bloqueo inmediato y fieldset disabled, validación de espacios/bytes, límites compartidos, mensajes y foco |
| `modules/autenticacion/Login.jsx` | Medio: todos los fallos se mostraban como contraseña incorrecta | mensajes de red, validación y límite de intentos según respuesta real |
| `shared/registration/FullRegistration.jsx` | Medio: límites de socios/nombre/CP no reflejaban backend | límites y formatos coherentes, dependientes calculados de solo lectura y fecha de nacimiento máxima |

## Validaciones agregadas

- Nombres de cuenta: Unicode y signos válidos preservados, espacios exteriores eliminados, longitud 1–160. No se inventó una prohibición general de números para nombres de proyectos/equipos o cuentas existentes.
- Correo: `EmailStr`, máximo 254 y minúsculas; índice único `lower(btrim(correo))`. Edición excluye el ID actual.
- Contraseñas: creación mínimo 8 caracteres; máximo 72 bytes UTF-8 por el bcrypt existente. Login admite contraseñas históricas cortas, sin recortar espacios. La edición con contraseña vacía conserva el hash.
- Progreso: entero JSON 0–100. Cupo: entero JSON 1–10000. Precio: número finito 0–100000 y hasta dos decimales. No se aceptan strings o booleanos numéricos.
- Fechas: AAAA-MM-DD, calendario real; horas locales sin zona ni segundos. La edición de eventos históricos continúa permitida. Se conserva Ciudad de México para agendas.
- Teléfonos: regla existente opcional de 10–20 caracteres (`0–9`, espacios, `+`, paréntesis y guiones). No se cambió arbitrariamente el formato de negocio.
- Estados y roles: literales existentes; booleanos exclusivamente `true`/`false`. IDs UUID y relaciones autorizadas comprobadas nuevamente en servidor.
- Registro completo: las reglas por campo están en `registration_fields.json`: texto 300, textarea 5000, nombre del proyecto/especialidad 160; opciones del selector exactas; cantidades finitas no negativas ≤1e9; cantidades enteras salvo ingresos con hasta dos decimales; CP de cinco dígitos; socios 1–20. Los requisitos solo se exigen al enviar, conservando el borrador parcial. La revisión administrativa usa la misma definición y el número de socios del registro original.
- Anexos del registro: 2 MiB cada uno y 20 MiB agregados, PDF/PNG/JPG; nombres sin rutas/control, contenido y dimensiones de imágenes comprobados. Documentos: 5 MiB, PDF/DOC/DOCX. Galerías: 8 MiB, cinco imágenes y normalización WebP existentes.
- Los uploads se descargan como adjuntos autorizados; los archivos existentes en S3 conservan sus llaves y metadatos. No se confía en el MIME del navegador.

## Cambios de tipos

Pydantic ahora distingue enteros, booleanos, precios y fechas sin coerciones peligrosas. UUID y fechas continúan viajando como strings JSON explícitos; no se activó strict global que rompiera esos contratos. El formulario completo conserva strings en JSON porque su formato admite borradores y campos heterogéneos; el servidor interpreta y valida cada campo según su especificación.

## Cambios de backend

Se mantienen las rutas existentes. Se añadieron esquemas compartidos (`schemas/validation.py`), DTOs para integrante/tipo de evento, middleware de tamaño, límites de login y preflight de migración. Los handlers mantienen las listas de campos permitidos: la propiedad viene del usuario autenticado; metadatos de pantalla enviados por clientes antiguos siguen siendo ignorados, sin asignarse a las entidades. Contraseñas y versión interna no aparecen en `/portal/state`.

## Cambios de base de datos

Migración Alembic `3a608b5c8533`, posterior a `295fe31b7422`:

- `usuarios.auth_version`: entero no nulo, default 0; compatible con la versión anterior durante el despliegue.
- Índices únicos de correos y tipos normalizados; índice parcial de tutoría confirmada por horario.
- CHECKs: nombre/correo de cuenta, progreso, cupo/precio/modalidad/estado de evento, intervalo de horario, nombre/estado de tarea, estado de tutoría, categoría/vigencia de publicación.
- Comprobación previa de duplicados y datos incompatibles. Si falla, PostgreSQL revierte la migración; no se eliminan ni corrigen datos de producción automáticamente.
- Reversión de aplicación: la imagen anterior puede utilizar el esquema ampliado. No es necesario revertir la BD para recuperar el servicio. Una bajada explícita de la migración eliminaría la nueva versión/índices/restricciones, sin borrar las tablas del negocio.

## Cambios de seguridad

Se mantienen consultas parametrizadas/ORM, permisos de rol y propiedad, transacciones con locks, unicidad de inscripciones, revisión de estados y S3 privado. React escapa el texto y el exportador CSV existente neutraliza fórmulas. La autenticación sigue siendo Bearer JWT: no se introdujeron cookies ni una nueva arquitectura. Los errores no devuelven contraseñas, archivos, SQL o stack traces. La revocación de contraseña/rol de coordinación no requiere almacenar JWTs en texto plano.

Las actualizaciones de dependencias se justifican por los [avisos del parser multipart](https://github.com/Kludex/python-multipart/security/advisories/GHSA-pp6c-gr5w-3c5g), su [parser urlencoded](https://github.com/Kludex/python-multipart/security/advisories/GHSA-5rvq-cxj2-64vf), [spooling de Starlette](https://github.com/Kludex/starlette/security/advisories/GHSA-2c2j-9gv5-cj73) y las [correcciones JWT](https://github.com/mpdavis/python-jose/releases/tag/3.4.0). Los endpoints existentes usan JSON o multipart; se rechaza urlencoded antes del parsing para mitigar el [límite ignorado en Starlette 0.x](https://github.com/Kludex/starlette/security/advisories/GHSA-82w8-qh3p-5jfq), sin forzar una actualización mayor de framework.

## Tests realizados

Resultados finales y datos del despliegue se registran en `docs/VERIFICACION_AUDITORIA.md`. Comandos previstos/ejecutados: `npm test`, `npm run build`, `python -m unittest discover -s tests -v` contra PostgreSQL temporal, construcción de `Dockerfile.production`, `git diff --check` y pruebas HTTPS del portal. Se agregaron casos de tipos estrictos, límites UTF-8, fechas, anexos falsificados, administración, errores sin datos sensibles y revocación de tokens.

## Problemas pendientes y límites

- `npm audit --omit=dev` informa dos avisos moderados de React Router 6. La corrección propuesta requiere Router 7; no se realizó una actualización mayor ajena a los formularios. El portal utiliza rutas internas controladas y no hidrata errores SSR. Debe planificarse esa actualización y revisar también los avisos de herramientas de desarrollo.
- El contador de login es por proceso; debe compartirse entre réplicas antes de ampliar el servicio. La configuración actual de ECS mantiene una tarea.
- El almacenamiento del JWT en localStorage y la duración existente se conservan; cambiar a cookies requiere un trabajo separado de contrato/CSRF. Las respuestas sensibles están marcadas no-store.
- Validar firma/tamaño de PDF o DOC no sustituye un antivirus ni una validación documental humana. No se añadió un servicio de análisis de malware sin infraestructura existente.
- Las pruebas automatizadas y de navegador cubren flujos y casos críticos, no constituyen una garantía de ausencia de defectos ni sustituyen la revisión institucional de datos reales y reglas de negocio.
