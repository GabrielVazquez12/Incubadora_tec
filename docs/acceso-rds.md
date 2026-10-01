# Consultar RDS desde EC2

La plantilla `infra/aws/database-access.yml` crea un cliente desechable en la
VPC de `incubadora-foundation`. Se administra mediante Session Manager, sin
SSH ni puertos entrantes. RDS permanece privada. La IPv4 pública permite que
el agente contacte SSM y descargue paquetes; no habilita conexiones entrantes.

El rol de la instancia puede leer únicamente el secreto de la cuenta de base
`incubadora_app`, además de los permisos de SSM. No recibe el secreto del
administrador de RDS ni el JWT del portal. El disco raíz está cifrado.

## Estado comprobado el 1 de octubre de 2026

- Stack: `incubadora-database-access`, creación completada.
- Instancia: `i-06d8b356596928765`, registrada en SSM como `Online`.
- Prueba por SSM Run Command: `Success`, cloud-init terminado.
- PostgreSQL: base `incubadora`, usuario `incubadora_app`, TLS activo y
  `transaction_read_only=on`. Conteo verificado: 3 usuarios.
- Validación de plantilla: cfn-lint y reglas cfn-guard de IMDSv2, disco cifrado,
  créditos CPU estándar y ausencia de clave SSH; sin fallos.

## Uso desde el navegador

1. En CloudFormation, abrir `incubadora-database-access` y copiar el output
   `InstanceId`.
2. En EC2, seleccionar esa instancia y abrir **Connect > Session Manager**.
3. Ejecutar `incubadora-db` para entrar a PostgreSQL.

```sql
\dt
SELECT nombre, correo, rol, creado_en FROM usuarios ORDER BY creado_en DESC;
\q
```

El cliente recupera la contraseña en memoria y valida el certificado TLS de
RDS. Las sesiones comienzan con transacciones de solo lectura y límite de 60
segundos por consulta. Esto previene cambios accidentales; no sustituye un
usuario PostgreSQL con privilegios exclusivamente de lectura. No se guarda
historial de psql en el disco.

## Uso desde PowerShell

Ejecutar el valor de `SessionCommand` del stack. Requiere AWS CLI autenticado
y el complemento local de Session Manager. Como alternativa, usar la consola
web, que no requiere instalar el complemento.

```powershell
aws ssm start-session --target i-06d8b356596928765 --profile incubadora-deploy --region us-east-1
```

La instancia y su IPv4 tienen costos mientras estén encendidas; el disco sigue
generando cargos cuando se detiene. Se puede detener cuando no se use y volver
a arrancarla para consultar. No almacena datos del portal.

## Instancias anteriores

Inventario de `us-east-1`, 1 de octubre de 2026:

| Instancia | Nombre | Observación |
|---|---|---|
| i-0d54cecd4b47df843 | incubadora-backend | VPC anterior; conservar hasta aclarar su uso |
| i-0754525e89d165db3 | incubadora-db-client | VPC anterior; no tiene perfil IAM de SSM |
| i-07b79204a618b534c | Proyecto-is-backend-env | Eliminada con autorización el 1 de octubre; entorno Terminated |

No se debe terminar solo la EC2 gestionada por Auto Scaling: el grupo la
recrearía. Antes de retirar el entorno anterior, conservar una instantánea del
disco y comprobar los recursos gestionados por Elastic Beanstalk.

El entorno `e-dkesz2rzfx` se eliminó después de completar al 100% la instantánea
`snap-0af935947ea74efab` del disco `vol-0a3b35e0d7c11897d`. Es una instantánea
del disco tomada con la instancia encendida, no un respaldo lógico de una base.
Se confirmó la EC2 en `terminated`, la desaparición de su Auto Scaling Group y
la liberación de `eipalloc-0734dbc18958f4667`. Se retiraron dos reglas obsoletas
que referenciaban exclusivamente el grupo eliminado `sg-06288c22047d934e6`:
`sgr-0c9814ea33d9650bf` y `sgr-0ae4600253a7f1d1d`. El entorno terminó en
`Terminated`. El portal actual respondió `ok` y la nueva EC2 permaneció encendida.
