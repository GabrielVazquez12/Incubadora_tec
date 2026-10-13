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
| `aws cloudformation validate-template --template-body file://infra/aws/application.yml ...` | Plantilla aceptada; no se modificó su estructura |

El frontend no tiene lint/formatter/typecheck configurados ni usa TypeScript. No se añadió una herramienta nueva para suplirlos. Las pruebas de interfaz existentes renderizan rutas con React; la prueba adicional de Chrome ejecuta la interfaz completa contra la API y PostgreSQL local.

La suite usa bases temporales y las elimina al terminar; no se conecta a RDS ni modifica datos reales. El portal de Chrome tiene una base independiente y un perfil propio. Los perfiles de prueba están excluidos de Git y Docker.

Durante la preparación hubo un timeout de una descarga Word mientras Docker construía. La repetición completa, con la construcción finalizada, pasó. El helper de Chrome se ajustó para esperar el arranque y enviar texto mediante eventos nativos; no se omitió la prueba fallida.

## Despliegue AWS

Pendiente de completar en esta misma actualización. Antes de modificar el servicio se ejecutará `preflight_forms.py` sobre RDS y se creará un respaldo. Después se aplicará Alembic en una tarea independiente y se revisará un change set que cambia únicamente la imagen. Los resultados definitivos, digest, revisión y comprobaciones HTTPS se registrarán aquí.

## Límites conocidos

`npm audit --omit=dev` informa dos avisos moderados de React Router 6; la corrección propuesta requiere Router 7. No se realizó esa actualización mayor. Los avisos, alcance y otros límites operativos están documentados en `AUDITORIA_FORMULARIOS.md`.
