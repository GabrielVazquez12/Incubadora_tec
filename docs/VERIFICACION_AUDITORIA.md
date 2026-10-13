# Verificación de la auditoría de formularios

Fecha: 13 de octubre de 2026. Repositorio: `Kike1196/Incubadora_tec`.
Rama: `fix/auditoria-formularios-tec`.

## Verificación local

| Comando | Resultado |
| --- | --- |
| `npm test` desde frontend | Aprobado: agenda, borradores, teléfonos, límites UTF-8, catálogos y comprobaciones de 56 páginas/53 enlaces |
| `npm run build` desde frontend | Aprobado: Vite compila el portal sin errores |
| `docker build --platform linux/amd64 -f Dockerfile.production -t incubadora-tec-audit:forms .` | Aprobado con las dependencias de seguridad actualizadas |
| `python -m unittest discover -s tests -v` dentro de la imagen de producción, conectado a PostgreSQL aislado | 33 pruebas aprobadas, sin skips; 184.566 segundos |
| `npm run test:browser` desde frontend, con portal local aislado en 127.0.0.1:8089 | Aprobado en Chrome real: registro, Unicode, doble envío, error de conexión al login, borrador parcial y fallo de actualización después de un guardado confirmado |
| Revisión de sintaxis mediante `ast.parse` | 68 archivos Python válidos |
| `git diff --check` | Sin errores |
| Suite completa después de retirar curl y sus dependencias de runtime | 33 pruebas aprobadas, sin skips; 99.403 segundos |
| `aws cloudformation validate-template --template-body file://infra/aws/application.yml ...` | Plantilla aceptada; no se modificó su estructura |

El frontend no tiene lint/formatter/typecheck configurados ni usa TypeScript. No se añadió una herramienta nueva para suplirlos. Las pruebas de interfaz existentes renderizan rutas con React; la prueba adicional de Chrome ejecuta la interfaz completa contra la API y PostgreSQL local.

La suite usa bases temporales y las elimina al terminar; no se conecta a RDS ni modifica datos reales. El portal de Chrome tiene una base independiente y un perfil propio. Los perfiles de prueba están excluidos de Git y Docker.

Durante la preparación hubo un timeout de una descarga Word mientras Docker construía. La repetición completa, con la construcción finalizada, pasó. El helper de Chrome se ajustó para esperar el arranque y enviar texto mediante eventos nativos; no se omitió la prueba fallida.

## Despliegue AWS

Código de formularios: commit `170572f`. Imagen final con reducción de paquetes: commit `198e4c4`; etiqueta inmutable `release-20261013-198e4c4`.

- Digest ECR: `sha256:b7540340efbece082aa73b074524d1c737522f76aeef903b457a033a237ce306`.
- Auditoría de solo lectura en RDS: tarea `27f5cc637a2849d9bb1ebf0bab97537a`, exit 0; todos los contadores de duplicados y datos incompatibles en cero.
- Respaldo RDS disponible al 100 %: `incubadora-forms-170572f-20261013155911`. Se conservó el respaldo; no se borraron ni modificaron automáticamente registros reales.
- Migración: tarea `f5c85acd92b7447b9101842b78f58d89`, exit 0; Alembic `295fe31b7422` → `3a608b5c8533`.
- Change sets `forms-170572f` y `forms-198e4c4`: validación CloudFormation sin hallazgos; únicamente actualización de Service sin reemplazo y nueva revisión de MigrationTask. Sin cambios de RDS, S3, red ni IAM.
- Definición final del servicio: `incubadora-application-Cluster-SxFBnh0m8Ory-incubadora-application-web:10`.
- `./scripts/verify-aws.ps1 -PortalFlow`: aprobado, exit 0; tarea `f575629776f9476786d6107bb13da5e7`, ejecutada con la imagen final.

La prueba HTTPS verificó conexión RDS con TLS y rol de aplicación, credenciales de tarea ECS, almacenamiento privado S3 con AES256 y carga/descarga, roles y acceso de estudiantes, galería editorial privada, publicaciones/borradores/vigencia, formato completo/aprobación/proyecto, documentos/revisión/permisos, avances/tareas/reportes, eventos/cupo/cancelación, asistencia/constancias PDF, Innovatec/corrección/etapas/historial/aislamiento, tutorías/reserva exclusiva/historial y solicitud externa/rechazo/corrección/admisión. Los pagos reales siguen deshabilitados según la configuración existente.

El escenario crea cuentas y registros sintéticos con identificadores aleatorios propios y los elimina en `finally`; confirmó la limpieza SQL y el borrado lógico de objetos temporales de S3. Las versiones antiguas de objetos permanecen bajo la política existente del bucket versionado.

Portal: [Incubadora en AWS](https://in-eba33374426a491eac5ff2c493e78050.ecs.us-east-1.on.aws). Estado final: CloudFormation `UPDATE_COMPLETE`; ECS con una tarea en ejecución, cero pendientes y despliegue completado, usando la imagen final y revisión 10. `/`, `/health` y `/api/health` responden 200 por HTTPS. `/api/portal/state` sin token responde 401 y contiene `X-Content-Type-Options: nosniff` y `Cache-Control: no-store`. Un login con correo inválido responde 422 sin reflejar la contraseña enviada.

La rama remota `fix/auditoria-formularios-tec` se confirmó con `git ls-remote destino refs/heads/fix/auditoria-formularios-tec`. Los contenedores y perfiles de Chrome usados exclusivamente para las pruebas locales se detuvieron o eliminaron al finalizar; no se tocaron recursos locales ajenos a esta auditoría.

## Límites conocidos

`npm audit --omit=dev` informa dos avisos moderados de React Router 6; la corrección propuesta requiere Router 7. No se realizó esa actualización mayor. ECR informa cero críticos, cinco altos, diez medios y tres bajos en la imagen final. Los cinco altos corresponden a CVE-2026-5435/CVE-2026-19499 (glibc), CVE-2026-93990/CVE-2026-77214 (Expat) y CVE-2026-85091 (zlib). Las versiones candidatas de los repositorios de Debian coinciden con las instaladas; no hay parche disponible allí al verificar. Los avisos, alcance y otros límites operativos están documentados en `AUDITORIA_FORMULARIOS.md`.
