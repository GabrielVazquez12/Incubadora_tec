# Retomar la conexión de documentos a AWS

Resumen del trabajo del 24 de septiembre, actualizado el 29 de septiembre de 2026.
No contiene contraseñas, tokens ni claves. Es un resumen de continuidad, no una
transcripción completa del chat.

## Objetivo del usuario

Conectar el módulo de documentos de Incubadora Tec a un bucket privado real
de S3, usando una identidad limitada en lugar de entregar credenciales raíz
al backend de Docker. El usuario autorizó crear el bucket y un usuario nuevo.

Repositorio: https://github.com/Kike1196/Incubadora_tec.git
Directorio: `C:\Users\loc_1\Incubadora_tec`.
La revisión inicial encontró los avances en `feature/kike` (commit `cb8fd64`),
mientras `main` apuntaba a `241a894`. Verificar de nuevo antes de publicar.
Los cambios realizados durante esta conversación no se han subido a GitHub.

## Implementación local terminada

- Panel Documentos del proyecto: carga PDF/DOC/DOCX, máximo 5 MB,
  descarga autorizada, revisión y observaciones.
- Estados: Pendiente, Aprobado y Correcciones solicitadas.
- Correcciones con conservación de versiones anteriores e historial.
- Integración S3 configurable y modo local PostgreSQL.
- Anexos de ingreso compatibles con S3; conservan la revisión del registro.
- Migración `a75c42e1b543` aplicada al entorno Docker local.
- Pasaron 15 pruebas del backend, compilación del frontend y verificaciones
  de interfaces antes de preparar la conexión AWS real.
- Guía de funcionamiento: `docs/documentos.md`.

## Recursos AWS creados y comprobados

Cuenta: `940827433988`. Región: `us-east-1`.

Bucket: `incubadora-tec-documentos-940827433988-us-east-1`.
Comprobado: bloqueo de acceso público completo, `IsPublic=false`, ACL
deshabilitadas (`BucketOwnerEnforced`), cifrado SSE-S3/AES256 y política
que exige HTTPS. Tiene cargos por almacenamiento y uso.

Usuario IAM: `incubadora-tec-desarrollo`.
Rol: `arn:aws:iam::940827433988:role/incubadora-tec-documentos-local`.

- El rol confía únicamente en el nuevo usuario.
- El rol permite GetObject, PutObject y DeleteObject únicamente bajo
  `expedientes/*` del bucket del proyecto.
- La simulación IAM confirmó esas acciones permitidas dentro de ese prefijo
  y denegadas fuera de él.
- El usuario puede asumir ese rol, cambiar su propia contraseña y consultar
  la política de contraseñas.
- Se adjuntó `SignInLocalDevelopmentAccess` para el inicio de sesión AWS CLI.
- No se crearon claves de acceso permanentes; se verificó que tiene cero.
- Perfil de consola creado con cambio obligatorio de contraseña.

Políticas reproducibles en `infra/aws/`:
`documentos-permissions.json`, `documentos-trust.json`,
`desarrollo-permissions.json`, `documentos-bucket-policy.json`,
`documentos-encryption.json` y `documentos-public-access.json`.

## Estado actual: conexión S3 activada y probada (29 de septiembre de 2026)

El usuario confirmó el cambio de contraseña y autorizó continuar con el login.
`aws login --profile incubadora-dev --region us-east-1` terminó correctamente.
STS confirmó `arn:aws:iam::940827433988:user/incubadora-tec-desarrollo`.
AWS CLI instalada: 2.36.28.

Se ejecutaron correctamente:

```powershell
./scripts/refresh-aws-documents.ps1
docker compose -f docker-compose.yml -f compose.s3.yml up -d backend
```

El backend usa `DOCUMENT_STORAGE=s3`. STS dentro del contenedor confirmó:
`arn:aws:sts::940827433988:assumed-role/incubadora-tec-documentos-local/incubadora-docker`.
El endpoint `http://localhost:8000/health` devolvió `status=ok`.

### Pruebas reales realizadas

- Carga y descarga de contenido idéntico mediante `app.document_storage`.
- Cifrado AES256 comprobado mediante HeadObject.
- Ejecutada la limpieza de la carga mediante rollback. La comprobación posterior
  esperaba NoSuchKey y recibió AccessDenied: sin ListBucket, S3 responde 403
  para objetos inexistentes. No se ampliaron los permisos del rol.
- Prueba HTTP `test_documentos_revision_correcciones_y_permisos` reutilizada
  con el servidor de pruebas configurado en S3 y una base PostgreSQL temporal.
  Resultado: OK, 1 prueba completa en 32.805 segundos.
- Cubrió carga, descarga, permisos, revisión, correcciones, aprobación,
  conflictos de estado y conservación del original e historial.
- Se comprobó en la base temporal que los dos documentos usaban el bucket real
  y no tenían contenido binario en PostgreSQL. Ambos objetos fueron eliminados
  con respuesta HTTP 204; también se eliminó la base temporal.
- La prueba HTTP se ejecutó mediante un adaptador temporal por stdin; los tests
  habituales siguen usando modo local y S3 simulado.
- No se hizo una nueva comprobación visual en el navegador en esta sesión.

Referencia para el 403 tras eliminar un objeto sin ListBucket:
https://docs.aws.amazon.com/AmazonS3/latest/API/API_GetObject.html

### Renovación y siguiente sesión

La sesión del rol dura una hora. No se inició renovación en segundo plano.
Para renovar durante el desarrollo, dejar abierta una terminal con:

```powershell
./scripts/refresh-aws-documents.ps1 -Watch
```

Si la sesión fuente expiró, autenticar de nuevo `incubadora-dev` conforme a la
habilidad signing-in-to-aws y después ejecutar el script. No usar root.
Antes de probar en una sesión futura, comprobar la identidad y renovar el rol.

El portal está en http://localhost:5173. Las nuevas cargas usan S3; los archivos
históricos locales siguen disponibles. No se desplegó el backend en AWS.

### Archivos de conexión y secretos

- `compose.s3.yml`: activa S3 y deja vacías las variables de claves estáticas.
- `backend/aws-documentos-config`: configura el proceso de credenciales.
- `backend/aws_document_credentials.py`: entrega la sesión solo al SDK.
  No ejecutarlo directamente en herramientas que impriman su salida.
- `scripts/refresh-aws-documents.ps1`: asume el rol y rechaza la identidad root.
- `backend/.aws-documentos-session.json`: sesión temporal protegida por ACL.
  Se confirmó que Git la ignora, igual que `.local/aws/usuario-temporal.json`.
- El archivo de contraseña temporal no se leyó ni se eliminó. La contraseña
  temporal ya fue cambiada por el usuario. Nunca publicar ese archivo.

No se montó ni exportó al backend la sesión CLI `default` de root. Tampoco se
modificaron el perfil `creative-agent`, otros usuarios IAM ni las políticas AWS.

## Notas operativas

La terminal restringida fallaba al iniciar con `helper_unknown_error:
setup refresh had errors`. Las operaciones se realizaron mediante
`exec_command` con escalación autorizada. No asumir que el fallo persiste:
verificar las condiciones de la siguiente sesión.

No sobrescribir cambios del usuario ni hacer push, merge o despliegue
suponiendo que ya ocurrieron. Consultar el estado actual de Git y AWS.
El archivo temporal de contraseña puede retirarse de forma segura después
de confirmar su cambio; nunca publicarlo ni copiarlo a la documentación.
