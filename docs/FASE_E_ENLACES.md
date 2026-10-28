# Fase E — difusión, eventos y vinculación

## Implementación

Se extienden las noticias, galerías, eventos e inscripciones existentes. No se agregan dependencias ni se modifica `.env`.

- Coordinación: calendario de piezas por canal, visitas realizadas, plantillas, registro manual de envíos, preguntas frecuentes, configuración y bandeja privada de contacto, fichas institucionales.
- Rutas públicas: `/difusion`, `/eventos`, `/eventos/:id`, `/vinculacion`, `/contacto` y `/aviso-de-privacidad`. FAQ configurables en Incubadora e InnovaTec; el pie muestra únicamente contactos/redes configurados o sus pendientes explícitos.
- Submenús dentro de Gestionar noticias y Eventos. La bienvenida autenticada conserva su contenido. Inicio enlaza al registro de Incubadora, inscripción de InnovaTec y difusión.
- Se conservan las noticias y sus galerías; los borradores, publicaciones futuras o caducadas no se hacen visibles mediante difusión. Los eventos utilizan el checkout existente; las fichas sin evento operativo no habilitan inscripción.
- Las tres propuestas institucionales se crean como borradores, sin fechas ni lugares inventados. No se crean eventos operativos al cargar propuestas.

## Datos y protección

La migración `526ccbbe0502`, posterior a encuestas, crea ocho tablas aditivas: `piezas_difusion`, `visitas_salon`, `plantillas_mensaje`, `envios_mensaje`, `preguntas_frecuentes`, `configuracion_enlaces`, `contactos_institucionales` y `fichas_evento`. Mantiene las tablas y datos anteriores. El downgrade se bloquea si cualquiera de las ocho contiene datos: un rollback de aplicación debe conservarlas.

Las APIs privadas exigen coordinación. Los DTO validan tipos, fechas, límites, responsables reales y enlaces HTTP/HTTPS sin credenciales. Las ediciones usan versión e historial. El texto de plantillas/envíos se serializa explícitamente solo en difusión, conservando la exclusión de contenido de archivos del serializador compartido.

El contacto público exige el aviso institucional aprobado y su versión actual, registra el consentimiento y conserva un único mensaje por folio. El bloqueo de la configuración de privacidad serializa reintentos concurrentes. Hay límite de frecuencia anónimo con claves hash, sin guardar direcciones IP en claro. La respuesta pública contiene solo folio y confirmación; la bandeja y las notas son privadas.

Los envíos son evidencia manual de comunicaciones ya realizadas; guardan una copia del texto y no envían correo ni mensajes. Las modificaciones posteriores de la plantilla no cambian la evidencia.

## Verificación

Cierre funcional verificado. Las pruebas nuevas cubren permisos, versiones obsoletas, enlaces/tipos inválidos, noticias no visibles, texto histórico de envíos, FAQ, configuración, privacidad, contacto concurrente y fichas sin fechas. La prueba de migración incluye conservación de datos ante rollback.

`npm test --prefix frontend` incluye rutas y límites por rol de la fase E. El recorrido reproducible de Chrome se ejecuta con `./scripts/verify-design-local.ps1 -InnovaTec -Incubadora -Encuestas -Difusion`; usa cuentas sintéticas y PostgreSQL/red/contenedores propios, elimina sus recursos al finalizar y guarda capturas en `.local/design-test-*`.

Resultados de esta reanudación:

- `npm test --prefix frontend`: aprobado, incluidas seis pantallas de coordinación, rutas públicas y exclusión por rol. Persisten avisos conocidos de `Navigate` al renderizar rutas protegidas con `StaticRouter`, sin fallos.
- `npm run build --prefix frontend` y build de producción Docker: aprobados. El último build compila 163 módulos.
- `./.local/verify-phase-a-backend.ps1`: 41 pruebas aprobadas en 132,799 s, con PostgreSQL temporal. Incluye comparación completa de esquema/migraciones y bloqueo de rollback con datos.
- `./scripts/verify-design-local.ps1 -InnovaTec -Incubadora -Encuestas -Difusion`: pasaron marca/menús, formularios, InnovaTec, Incubadora y encuestas; detectó un fallo nuevo al navegar de lista a detalle de eventos. Se corrigió montando estado remoto independiente por ruta. Capturas de regresiones anteriores: `.local/design-test-abfb3efe170540ef923400c07b628467`.
- `./scripts/verify-design-local.ps1 -OnlyDifusion`: aprobado después de la corrección, con operaciones de piezas/visitas/plantillas, registro manual, FAQ, configuración, pie, contacto con doble envío, revisión privada y ficha pública. Trece capturas finales en `.local/design-test-8ac52138044e4b8db8b44a73ae879697`; revisadas visualmente calendario móvil, bandeja privada móvil, detalle de evento móvil y difusión pública de escritorio.
- `node --check frontend/scripts/browser-helper.cjs`, `node --check frontend/scripts/difusion-browser.cjs` y `git diff --check`: aprobados. Git solo advierte la conversión habitual de LF a CRLF.

La primera suite backend detectó la exclusión de texto por el serializador compartido y un timeout de descarga Word durante carga concurrente. La exclusión se corrigió en difusión; la suite completa pasó al repetirla sin otra regresión simultánea. La primera sesión de Chrome bloqueada se detuvo y se añadieron límites de espera; las ejecuciones posteriores terminaron y limpiaron sus recursos temporales.

No hay formatter, linter ni typecheck configurados en este proyecto. El runner de Chrome ahora limita cada comando a 30 segundos y fuerza el cierre de su proceso si no responde.

## Pendientes institucionales y publicación

Siguen pendientes contactos, redes, fechas, sedes y aviso de privacidad reales aprobados. No se precargan personas, mensajes o participación reales. El formulario público permanece cerrado hasta configurar el aviso aprobado.

La fase F y el despliegue conjunto son trabajo posterior. Esta integración no aplica migraciones ni cambios en AWS.

## Archivos principales

- Backend: `app/models/enlaces.py`, `app/schemas/enlaces.py`, `app/modules/difusion/routes.py`, registro de modelos/rutas y límite de contacto en `app/auth/rate_limit.py`.
- Migración: `backend/alembic/versions/526ccbbe0502_difusion_vinculacion_y_fichas_de_.py`.
- Frontend: `src/modules/difusion/Outreach.jsx`, `outreach.css`, `App.jsx`, `PortalLayout.jsx`, `InstitutionalFooter.jsx`, `Landing.jsx`, `Incubation.jsx` y `PublicInnova.jsx`.
- Pruebas: `backend/tests/test_portal.py`, `test_migraciones.py`, `frontend/scripts/interface-checks.jsx`, `difusion-browser.cjs`, `browser-helper.cjs` y `scripts/verify-design-local.ps1`.
- Se conservaron las correcciones móviles previas de `surveys.css` e `incubation.css`, comprobadas con las regresiones de sus módulos.
