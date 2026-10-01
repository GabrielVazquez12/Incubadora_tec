# Operacion del portal AWS

## Comprobacion del 1 de octubre de 2026

La prueba `./scripts/verify-aws.ps1 -PortalFlow` termino con codigo cero sobre
el portal HTTPS publicado. Valida por API:

- Login de estudiante y coordinacion; panel administrativo accesible solo al admin.
- Envio del formato de registro con anexos y aprobacion por coordinacion.
- Creacion del proyecto a partir del registro aprobado.
- Carga y descarga de un documento privado; rechazo a un usuario ajeno.
- Revision administrativa del documento y cambio de estado del proyecto.
- Visibilidad de ambos cambios desde la cuenta estudiante.

Se usaron cuentas, registro, proyecto y documentos temporales con identificadores
unicos. Los registros SQL se eliminaron al terminar; en S3 se aplica borrado
logico, por lo que el versionado puede conservar versiones anteriores. La prueba
no cambia la cuenta administradora real ni requiere conocer su contrasena.
No sustituye una inspeccion visual del navegador con el usuario real.

La prueba crea datos en el entorno elegido: ejecutar de forma deliberada. Puede
repetirse usando `-Profile`, `-Region`, `-FoundationStack` y `-ApplicationStack`.
La tarea ECS usa la imagen actualmente desplegada, sin reconstruirla.

## Alertas preparadas, pendientes de activar

`infra/aws/monitoring.yml` incluye:

- Ausencia de contenedores sanos durante tres minutos.
- Cinco o mas errores HTTP 5xx del backend en cinco minutos.
- Menos de 2 GiB de espacio libre en RDS durante tres minutos.
- Presupuesto mensual de toda la cuenta, excluyendo creditos y reembolsos,
  con avisos al superar 80%, 100% y proyeccion superior al 100%.

Faltan el correo receptor y el importe mensual elegidos por el usuario. No usar
`admin.demo@example.com` como destino: es un correo de ejemplo, no un buzon confirmado.
El presupuesto avisa, pero no detiene recursos ni impone un limite de cobro.
Las alarmas, SNS y la clave KMS pueden generar cargos. Los correos operativos
requieren confirmar la suscripcion SNS; no basta con crear el stack.

Parametros requeridos: `NotificationEmail`, `MonthlyBudgetUsd`,
`DatabaseIdentifier`, `LoadBalancerFullName`, `TargetGroupFullName`.
Los dos ultimos deben corresponder al balanceador y al grupo de destinos de la
revision ACTIVA del servicio; una revision anterior puede mantener otro grupo.
Usar los sufijos `app/nombre/id` y `targetgroup/nombre/id`, no los ARN completos.

Validar con cfn-lint y `infra/aws/monitoring.guard`, preparar un change set,
consultar `describe-events`, revisar cambios y ejecutar. Confirmar la suscripcion
de correo y probar la ruta de notificacion antes de considerar activas las alertas.

## Respaldos y restauracion

Se comprobo RDS `available`, retencion automatica de un dia y estos snapshots
automaticos cifrados en estado `available`:

- `rds:incubadora-foundation-database-zuqiwmta85oz-2026-09-30-15-11`
- `rds:incubadora-foundation-database-zuqiwmta85oz-2026-10-01-06-50`

La API tambien informo `LatestRestorableTime=2026-10-01T21:46:23Z`.
Son datos de una comprobacion puntual; volver a consultarlos antes de restaurar.

**La restauracion completa aun no se ha probado.** El plan FREE rechazo antes
una tercera RDS y siguen existiendo dos instancias. No eliminar una base existente
ni cambiar el plan de facturacion automaticamente para liberar espacio.

Cuando haya capacidad autorizada:

1. Elegir un snapshot disponible o un punto de restauracion valido.
2. Restaurar a una instancia temporal con otro identificador, cifrada y privada,
   en el mismo grupo de subredes de RDS y con acceso solo desde el grupo autorizado.
3. Desde EC2, conectarse al endpoint temporal con TLS y consultar la revision de
   Alembic, las tablas y conteos. No apuntar el portal al clon durante el ensayo.
4. Registrar duracion y resultados. El contenido de documentos permanece en S3;
   restaurar RDS no recupera por si solo versiones borradas de los objetos.
5. Retirar unicamente el clon de prueba, conservando la base original y el snapshot.

## Pendientes que requieren informacion

- Correo real e importe mensual para activar alertas.
- Disponibilidad de capacidad para probar la restauracion RDS.
- Dominio propio, si se desea; el dominio HTTPS de AWS ya funciona.
- Proveedor y cuenta de pagos si se cobrara desde el portal. Los pagos demo
  permanecen desactivados; no se habilitan cobros durante las pruebas.
