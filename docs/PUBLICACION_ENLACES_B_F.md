# Publicación AWS de Enlaces Institucionales ITS — fases B–F

Despliegue completado y verificado el 14 de octubre de 2026. [Portal publicado](https://in-eba33374426a491eac5ff2c493e78050.ecs.us-east-1.on.aws). La optimización adicional del rendimiento móvil sigue pendiente: Lighthouse sobre producción dio 80, frente a 93 en la verificación local.

## Versión activa

- Código de aplicación: `da17bde9e2ef668a5b629e9fbd3ccadca5ecaf4a`. Configuración de proxy: `f1ba9e196b07eb0deb920ffaeb66928fcaac9f47`. Rama publicada: `feat/enlaces-institucionales-its`, remoto `destino`.
- Imagen: `enlaces-bf-da17bde`.
- Digest activo confirmado: `sha256:3d93e2ea00087e180de64ec6517fbef53898dd61874d4a1fafcae7be78b2d523`; manifiesto Linux: `sha256:87d0b3227ba2a24298a3cd324250e9bb81dd9a87e84c4a73ee2a4b3932e6b9e6`.
- CloudFormation `UPDATE_COMPLETE`; ECS `COMPLETED`, revisión `:15`, una tarea activa y cero pendientes. Comprobación: `2026-10-14T13:32:24.2413481-06:00`.
- Esquema real: `637ddccf1603`. Las cinco migraciones B–F se aplicaron mediante una tarea independiente con código 0, manteniendo la versión anterior activa durante el proceso.
- Se conservaron RDS, S3, IAM y red. Los planes de publicación solo modificaron el servicio sin reemplazo y la definición de tarea de migración; el ajuste final de proxy solo modificó Service.

## Respaldo y recuperación

- Snapshot RDS disponible al 100 %: `incubadora-enlaces-bf-20261014112430`.
- Copia lógica en el bucket privado existente, cifrada AES256: `expedientes/backups/enlaces-bf-ea2d990/backup.dump`. Versión S3: `xFAyKJVIeQkXmQcPAvK.NygO_S.Ap.u0`.
- SHA-256 comprobado tras descargar la copia dentro de ECS: `0f6ad5b06535a40afbfc074891a32fd3fa164409a37fef904c0fd288d7b67df9`.
- Restauración lógica y ensayo de migraciones aprobados. Las 18 tablas anteriores conservaron exactamente sus filas y valores en el ensayo. Los datos reales no se descargaron al equipo local.
- Fuente RDS PostgreSQL 15.19; restauración temporal PostgreSQL 17. La restauración física del snapshot a otra RDS fue bloqueada por `InstanceQuotaExceeded` del plan gratuito; no queda acreditada una restauración física ni una restauración lógica en PostgreSQL 15. No se cambió el plan.
- Preflight: código 0 y todas las incompatibilidades en cero. Tarea `069d516ee75e476cba9c791c506ff824`. Ensayo `b2b972c6e0aa4311955c600c93fff0c9`. Migración real `8c1868324baf4503852d8956471d9097`.

## Verificación

- `docker build --platform linux/amd64 -f Dockerfile.production -t incubadora-tec-audit:phase-a .`: aprobado. Sin nuevas dependencias de aplicación.
- `.local/verify-phase-a-backend.ps1`: 45 pruebas aprobadas en 136,663 s con PostgreSQL 15 aislado; incluye migraciones, permisos, revocación, auditoría y proxy confiable/no confiable.
- Frontend: pruebas de 56 páginas y 78 enlaces, build y regresión Chrome B–F aprobados antes de publicar; no hubo cambios posteriores en la interfaz.
- `cfn-lint` 1.57.1, `cfn-guard` 3.2.1 con `infra/aws/application.guard`, `cloudformation validate-template` y validación de change sets: aprobados.
- `./scripts/verify-aws.ps1 -PortalFlow`: código 0, tarea `4448eb3b712b401fab7ea24c52077654`. Verificó RDS/TLS, rol ECS, S3/AES256, acceso/restricciones, noticias, documentos privados, registros/proyectos, eventos/cupos/asistencia/constancias, InnovaTec, tutorías y solicitudes externas. Sus registros SQL y objetos S3 temporales se retiraron.
- Comprobación pública: 13 rutas con títulos y canónicos HTTPS, sitemap y robots, ausencia de indexación privada, 401 sin token, 403/404 correctos y caché de assets compilados.
- Escaneo ECR Linux COMPLETE: 0 críticos, 5 altos, 10 medios y 3 bajos; mismas cantidades pendientes de la imagen de fase A.
- No hay formatter, linter de aplicación ni typecheck configurados. La validación de infraestructura sí se ejecutó.

Lighthouse 13.5.0 sobre el sitio real:

| Categoría | Móvil | Escritorio |
|---|---:|---:|
| Rendimiento | 80 | 100 |
| Accesibilidad | 100 | 100 |
| Buenas prácticas | 100 | 100 |
| SEO | 100 | 100 |

Móvil: FCP 1,56 s, LCP 1,70 s, TBT 822,5 ms, CLS 0; respuesta del servidor 72 ms. El bloqueo de ejecución requiere optimización adicional. No se atribuye automáticamente al backend ni se presenta la medición local 93 como resultado de producción.

Informes HTML/JSON: `.local/enlaces-bf-live-20261014130427`. Evidencias de estado y rutas: `.local/enlaces-bf-final-service.json` y `.local/enlaces-bf-public-result.json`. Las herramientas y evidencias locales permanecen fuera de Git.

## Metadata HTTPS y operación

La aceptación detectó enlaces http detrás del balanceador HTTPS. `public_origin` usa `X-Forwarded-Proto` exclusivamente para metadata, con valores http/https y pares de red configurados. Los rangos reales del balanceador, confirmados por ELB/EC2 y logs, son `10.42.1.0/24,10.42.2.0/24`. Fuentes no confiables, cabeceras inválidas y falta de configuración no alteran el esquema. No cambia la IP usada por autenticación ni amplía permisos.

Las tareas temporales terminaron; se desregistraron sus definiciones propias. Los contenedores locales de prueba se retiraron; no se modificaron `bycode-web-1` ni `bycode-backend-1`. No se modificó `.env`.

## Reversión y pendientes

Conservar snapshots, copia S3 y las imágenes anteriores. Una reversión de aplicación mantiene el esquema ampliado: nunca ejecutar downgrade destructivo, borrar datos ni reemplazar RDS. Una versión anterior no interpreta los perfiles complementarios; revisar los permisos técnicos antes de revertir. Procedimiento de administración y recuperación: `GUIA_ADMINISTRACION_ENLACES.md`.

Pendientes: optimización móvil de producción, revisión de hallazgos heredados de imagen y prueba física de recuperación RDS cuando exista capacidad. También faltan los contenidos institucionales aprobados: aviso, contactos/redes, convocatoria/manual, fechas/sedes y criterios de operación. El formulario público continúa sujeto al aviso aprobado. Designar al primer Administrador con una cuenta real de coordinación siguiendo la guía; no se crean cuentas institucionales ficticias.
