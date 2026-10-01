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

## Alertas desplegadas el 1 de octubre de 2026

Stack `incubadora-monitoring`: `CREATE_COMPLETE`. Presupuesto mensual
`incubadora-monitoring-account-monthly`: USD 20 para toda la cuenta, con
destinatario indicado por el usuario en los parametros del stack. Se conservó
el presupuesto anterior `Escuela`. Las tres alarmas fueron creadas y al inicio
estaban en `INSUFFICIENT_DATA`, a la espera de evaluar métricas.

La entrega de alertas operativas requiere confirmar el correo de SNS. No se
ha probado todavía la entrega de extremo a extremo.

`infra/aws/monitoring.yml` incluye:

- Ausencia de contenedores sanos durante tres minutos.
- Cinco o mas errores HTTP 5xx del backend en cinco minutos.
- Menos de 2 GiB de espacio libre en RDS durante tres minutos.
- Presupuesto mensual de toda la cuenta, excluyendo creditos y reembolsos,
  con avisos al superar 80%, 100% y proyeccion superior al 100%.

El usuario proporcionó el correo receptor y el importe mensual. El correo se
configuró como parámetro de despliegue y no se guarda en este documento.
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

## Reduccion de gasto: 1 de octubre de 2026

Se confirmó el estado `stopped` de las EC2 anteriores `i-0d54cecd4b47df843` y
`i-0754525e89d165db3`, y el cliente de consultas `i-06d8b356596928765`.
Se conservaron sus discos. El cliente no tenía sesiones SSM activas; se puede
encender siguiendo `docs/acceso-rds.md`. El portal funciona en ECS Fargate;
después de detenerlas, `/health` respondió `ok` y PostgreSQL estaba `available`.

Con tarifas consultadas de USD 0.0104/h por t3.micro y USD 0.005/h por IPv4,
730 horas sin las tres instancias representan aproximadamente USD 33.73 menos
de consumo mensual. Excluye EBS, que sigue generando cargos; encender el cliente
reduce el ahorro. Es una estimación de consumo, no de factura tras créditos.

La RDS MySQL antigua `incubadora-db` se conserva: los máximos horarios de
DatabaseConnections consultados entre el 24 de septiembre y el 1 de octubre
fueron cero. Esto no demuestra que sus datos carezcan de valor. Su eliminación
y respaldo final requieren una decisión explícita.

Existe un presupuesto mensual `Escuela` de USD 1; no se modificó. La plantilla
de monitoreo se desplegó después con un presupuesto adicional de USD 20.

## Informacion pendiente

- Confirmación de la suscripción SNS y prueba de entrega de alertas operativas.
- Disponibilidad de capacidad para probar la restauracion RDS.
- Dominio propio, si se desea; el dominio HTTPS de AWS ya funciona.
- Proveedor y cuenta de pagos si se cobrara desde el portal. Los pagos demo
  permanecen desactivados; no se habilitan cobros durante las pruebas.
