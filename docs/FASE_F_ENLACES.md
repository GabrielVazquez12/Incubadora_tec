# Fase F — perfiles, auditoría, SEO y verificación

Plan: `PLAN_FASE_F.md`. Guía operativa: `GUIA_ADMINISTRACION_ENLACES.md`.

## Cambios

Perfiles complementarios Asesor y Administrador, revocables y sin modificar roles técnicos/enum. Bootstrap de Administrador desde coordinación, versión e historial, protección del último Administrador y de sus credenciales frente a coordinadores sin esa capacidad. Cada cambio de perfil invalida sesiones.

Acceso del asesor exclusivamente a expedientes asignados y sus documentos, sin ampliar el helper global de acceso a proyectos. Solo puede registrar diagnóstico, asesoría y seguimiento a su cargo. Asignación y atención reutilizan el modelo y las reglas de Incubadora existentes. Nuevas pantallas cargadas de forma diferida y submenús bajo Roles.

Auditoría transaccional general de escrituras autenticadas, con actor/entidad/id/operación/campos y sin valores sensibles. API de consulta paginada reservada a Administrador. Sin API de mutación y con bloqueo ORM de edición/borrado. Límites y operación documentados en la guía.

Migración `637ddccf1603` posterior a E: `perfiles_acceso` y `auditoria_acceso`; aditiva, sin cambios en datos anteriores. Downgrade bloqueado con datos.

Manifest compartido de metadata entre React y el HTML del servidor, enlaces canónicos/OG públicos, noindex privado, robots/sitemap sin datos de usuarios, 403/404 accesibles con códigos HTTP, cabeceras de protección, compresión y caché para assets compilados.

No se agregaron dependencias de aplicación. Lighthouse 13.5.0 se ejecuta como herramienta temporal; package.json y lockfile no cambian por ello. No se modificó `.env` ni infraestructura de producción.

## Verificación final

Verificación completa aprobada: 44 pruebas backend en 95,576 s; pruebas frontend con 56 páginas y 78 enlaces; build de producción y regresión completa en Chrome de las fases B–F. Se verificaron bootstrap, aislamiento del asesor, documentos privados, revocación, protección del cambio de rol, atomicidad e inmutabilidad ORM de auditoría, migraciones y SEO.

Lighthouse 13.5.0 local:

| Categoría | Móvil | Escritorio |
|---|---:|---:|
| Rendimiento | 93 | 100 |
| Accesibilidad | 100 | 100 |
| Buenas prácticas | 100 | 100 |
| SEO | 100 | 100 |

Artefactos finales: `.local/design-test-cff003fffc304cf5a420d2838d9fbef3`, incluidos los informes HTML/JSON de Lighthouse y capturas de perfiles, expediente, auditoría, revocación, boletín y recuperación de carga.

La entrada JavaScript pasó de aproximadamente 486 kB / 146 kB gzip a 283 kB / 94 kB gzip mediante carga por páginas. El boletín de inicio se carga al acercarse a pantalla; los enlaces directos a noticias mantienen su apertura. Se prioriza la imagen principal, se limita la precarga de fuentes a escritorio y se difiere el render del pie fuera de pantalla. Chrome verificó también recuperación tras un fallo de carga de página.

Limitación de captura: las capturas de página completa pueden mostrar vacío el pie fuera de pantalla por `content-visibility`; no equivalen a una captura del pie visible al desplazarse. Las métricas son locales y deben repetirse tras el despliegue real.

No se hicieron commits, push, despliegues ni migraciones de producción en esta reanudación.

## Archivos principales

- Backend: `app/access.py`, `app/auditing.py`, `app/seo.py`, `app/models/gobierno.py`, `app/modules/gobierno/routes.py`, integración en autenticación, coordinación, Incubadora y servidor de producción.
- Migración: `backend/alembic/versions/637ddccf1603_perfiles_y_auditoria_aditivos.py`.
- Frontend: `App.jsx`, rutas y protección, `modules/gobierno/`, `shared/portal/lazyPage.jsx`, `shared/design/Seo.jsx`, `shared/design/AccessDenied.jsx`, `public/site-pages.json`, boletín y estilos públicos.
- Verificación: pruebas backend de portal, migraciones y SEO; `frontend/scripts/governance-browser.cjs`, `performance-browser.cjs`, helper y pruebas de interfaz; `scripts/verify-design-local.ps1`.
- Documentación: este informe, guía de administración, README y punto de reanudación.

Comandos reproducibles:

- `npm test --prefix frontend`.
- `docker build --platform linux/amd64 -f Dockerfile.production -t incubadora-tec-audit:phase-a .`.
- `python -m unittest discover -s tests -v` desde backend con PostgreSQL aislado; el runner local `.local/verify-phase-a-backend.ps1` crea su propia red/base/contenedor y los elimina.
- `./scripts/verify-design-local.ps1 -SkipBuild -InnovaTec -Incubadora -Encuestas -Difusion -Gobierno -Lighthouse` para toda la regresión y Lighthouse móvil/escritorio.
- `./scripts/verify-design-local.ps1 -OnlyGobierno -Lighthouse` para repetir F de forma aislada.
- `git diff --check`, y `node --check` para los runners de navegador.

No existen formatter, linter ni typecheck configurados. No se declaran aprobados. Persisten warnings anteriores de Navigate/StaticRouter en las pruebas de render estático, sin errores.
