# Publicación del diseño A en GitHub y AWS

Código de aplicación: `224db78`, rama `feat/enlaces-institucionales-its` en `Kike1196/Incubadora_tec`. Imagen: `editorial-a-224db78`.

La portada incorpora la composición editorial seleccionada, conserva el Newsletter conectado a su API y agrega misión y visión institucionales resumidas, contacto telefónico de Vinculación y ubicación del campus. Las fuentes oficiales se enlazan en la página. No se agregaron dependencias ni se modificaron backend, esquema o variables de entorno.

Validación previa: pruebas del frontend (incluidas 56 páginas y 78 enlaces), compilación Vite de 170 módulos, Chrome a 1440/390/320 px, búsqueda y lectura del Newsletter, y `git diff --check`, aprobados. No hay linter, formateador ni typecheck configurados. La advertencia de Navigate en StaticRouter durante las pruebas es conocida. No se repitió Lighthouse ni la suite backend para este cambio exclusivo de interfaz.

El plan usa la plantilla ya desplegada y cambia únicamente el parámetro ImageTag. Modifica Service sin reemplazarlo y reemplaza la definición de MigrationTask al actualizar su imagen; no ejecuta la tarea de migración. Sin modificaciones de RDS, S3, IAM ni red.

Escaneo ECR del manifiesto Linux: COMPLETE, 0 críticos, 5 altos, 10 medios y 3 bajos, mismas cantidades que la publicación anterior. La corrección de esos hallazgos heredados queda pendiente.

Reversión de aplicación: restaurar el parámetro ImageTag a `enlaces-bf-da17bde` mediante un change set revisado de la misma plantilla. No ejecutar downgrade ni operaciones de borrado de datos.

## Estado final y aceptación

Publicación completada: `2026-10-14T15:54:11.6585664-06:00`. [Portal publicado](https://in-eba33374426a491eac5ff2c493e78050.ecs.us-east-1.on.aws).

- CloudFormation: `UPDATE_COMPLETE`.
- ECS: revisión `:16`, rollout `COMPLETED`, una tarea activa y cero pendientes; revisión anterior retirada.
- Digest de imagen publicado y confirmado en la tarea: `sha256:dec31e96673e6920920106320495515148c595848b52c0d6e25f8baaa23e873f`.
- Manifiesto Linux: `sha256:112f9777949e7a97785d0db665ad6222ed76033164fb9e8838bb8eef221e9fa6`.
- Chrome sobre HTTPS real: 1440, 390 y 320 px, portada A y secciones presentes, un solo h1, sin desbordamiento ni errores de ejecución. Newsletter dinámico con cinco publicaciones: búsqueda, recuperación de resultados, lectura en diálogo y cierre con Escape aprobados.
- Ocho comprobaciones HTTP 200: inicio, Incubadora, InnovaTec, Vinculación, Eventos, Contacto, API público del Newsletter y salud.
- No se modificaron datos de producción ni se ejecutaron migraciones. Se conservan el aviso y las restricciones existentes del formulario público de contacto.

Evidencia local fuera de Git: `.local/editorial-deployment.json`, `.local/editorial-final-service.json`, `.local/editorial-live-checks.json`, `.local/editorial-public-http.json` y capturas `.local/editorial-live-*.png`.

Pendiente editorial: confirmar edificio, horario de atención y otras sedes de Vinculación antes de agregarlos. La ubicación publicada corresponde al campus ITS, no a una oficina específica verificada.
