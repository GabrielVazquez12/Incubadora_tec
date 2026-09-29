# Documentos y anexos privados

## Uso

En el detalle de un proyecto, **Documentos del proyecto** permite subir PDF,
DOC y DOCX de hasta 5 MB. El propietario, los integrantes y coordinación
pueden subir y descargar documentos del proyecto. Otras cuentas y usuarios
sin sesión no tienen acceso. Los anexos personales del registro mantienen
su acceso restringido al solicitante y coordinación, no a los integrantes.

Cada documento nuevo queda **Pendiente**. Solo coordinación puede aprobarlo
o solicitar correcciones. Solicitar correcciones requiere observaciones.
El estudiante utiliza **Enviar corrección**: se crea un documento pendiente,
la versión anterior sigue descargable y conserva su revisión. El historial
registra fecha, responsable, resultado y observaciones. La API rechaza una
revisión si el estado cambió desde que se abrió el formulario.

Los anexos de ingreso mantienen la revisión dentro del formato de registro;
los nuevos estados individuales corresponden a documentos del proyecto.

## Desarrollo local

`DOCUMENT_STORAGE=local` guarda los archivos en PostgreSQL, como antes.
No requiere credenciales AWS ni genera consumo de S3. Los límites y permisos
son iguales en ambos modos. La vista previa no permite cargas ni revisiones
reales. Para actualizar una instalación existente:

```powershell
docker compose exec -T backend alembic upgrade head
```

La migración agrega columnas de revisión sin borrar archivos ni proyectos.

## Activar S3

### Conexión local con sesión temporal

Bucket del proyecto: `incubadora-tec-documentos-940827433988-us-east-1`,
región `us-east-1`. Sus políticas están en `infra/aws/`.
La conexión mediante `compose.s3.yml` evita entregar al contenedor el perfil
de administración de Windows. Requiere que un administrador configure el rol
`incubadora-tec-documentos-local` y autorice a la identidad IAM del desarrollador.

La identidad creada para este entorno es `incubadora-tec-desarrollo`, en la
cuenta `940827433988`. Su política permite asumir únicamente el rol de
documentos, cambiar su propia contraseña e iniciar sesión con AWS CLI.
No tiene claves de acceso permanentes. El rol confía únicamente en ese usuario.
Los archivos `desarrollo-permissions.json` y `documentos-trust.json` documentan
los permisos y la relación de confianza. La primera entrada a la consola exige
cambiar la contraseña temporal entregada localmente fuera de Git.

Después de autenticar el perfil `incubadora-dev` y configurar ese rol:

```powershell
./scripts/refresh-aws-documents.ps1
docker compose -f docker-compose.yml -f compose.s3.yml up -d backend
```

El script rechaza la identidad raíz y obtiene una sesión del rol limitada al
prefijo `expedientes/`. La guarda en `backend/.aws-documentos-session.json`,
excluido de Git y con permisos Windows restringidos. El SDK la lee mediante
`credential_process`; no es necesario instalar AWS CLI dentro del contenedor.
No mostrar ni ejecutar directamente `aws_document_credentials.py`: su salida
es el protocolo privado de credenciales del SDK.

Para renovar mientras trabajas, dejar abierta una terminal ejecutando:

```powershell
./scripts/refresh-aws-documents.ps1 -Watch
```

Si la sesión de origen termina, volver a autenticar el perfil y ejecutar el
script. Este mecanismo es para desarrollo local; en un despliegue AWS se usa
el rol del servicio de cómputo. La activación y la prueba real dependen de
completar primero el acceso IAM, no basta con que exista el bucket.

### Configuración alternativa mediante variables

Configurar en `backend/.env` (el contenedor monta ese directorio):

```dotenv
DOCUMENT_STORAGE=s3
AWS_S3_BUCKET=nombre-del-bucket-privado
AWS_REGION=us-east-1
```

Reiniciar el backend después de cambiar la configuración. El bucket debe
existir en la región indicada. La aplicación no crea ni publica buckets.
Usar un rol IAM del servicio en producción; para desarrollo se admite la
cadena de credenciales del SDK o las variables `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY` y `AWS_SESSION_TOKEN` para credenciales temporales.
Nunca poner credenciales en el frontend, el repositorio o capturas de pantalla.

En el bucket configurar bloqueo de todo acceso público, Object Ownership
`Bucket owner enforced` (ACL deshabilitadas) y cifrado predeterminado SSE-S3.
Las cargas solicitan explícitamente AES256 y no añaden ACL públicas.
Una política del bucket debe denegar operaciones con `aws:SecureTransport=false`.
El rol del backend necesita únicamente estas acciones sobre el prefijo usado:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
    "Resource": "arn:aws:s3:::NOMBRE_DEL_BUCKET/expedientes/*"
  }]
}
```

`DeleteObject` se utiliza para retirar cargas cuya transacción no se confirmó.
No se necesita CORS de S3: la API recibe y valida el archivo, y sirve su
descarga después de comprobar el permiso. No se envían claves S3 ni URLs
públicas al navegador. El tipo declarado por el navegador no se considera
prueba del formato; se comprueban extensión y firma, y la estructura ZIP
en DOCX. Esto no sustituye un análisis antivirus.

Si se integra un servicio AWS mediante política de recursos, limitar su
principal y usar `aws:SourceAccount`/`aws:SourceArn` según corresponda.
Habilitar registros de acceso del bucket, eventos de datos de CloudTrail y
métricas/alertas de CloudWatch; cifrar también sus destinos de logs.

## Compatibilidad, fallos y retención

- Las nuevas cargas usan el modo configurado. Si S3 falla, la API devuelve
  un error; no cambia silenciosamente al almacenamiento local.
- Los documentos históricos en PostgreSQL siguen descargándose. No se
  trasladan automáticamente por cambiar la variable.
- Los anexos de un registro editable se trasladan a S3 al siguiente guardado
  exitoso del solicitante. Los registros aprobados conservan sus anexos
  anteriores y siguen descargándose.
- Los anexos permiten PDF, PNG y JPG, hasta 2 MB cada uno y 20 MB en conjunto.
  La base conserva metadatos, no el contenido, cuando se guardan en S3.
- Ante un rollback se intenta eliminar cada objeto recién subido. Si AWS
  tampoco permite limpiarlo, se registra la clave en el log del servidor
  para conciliación. Una caída del proceso entre S3 y el commit también
  puede dejar objetos sin referencia; no hay una transacción distribuida.
- Se conservan versiones anteriores de documentos del proyecto. Los objetos
  S3 de anexos reemplazados también se retienen, pero no aparecen en la UI.
  Definir una política de retención antes de una limpieza; no configurar
  caducidad global del prefijo porque eliminaría expedientes vigentes.

S3 tiene cargos por almacenamiento, solicitudes y transferencia; conservar
versiones y activar auditoría añade consumo. La aplicación no provisiona
recursos de pago. Consultar [precios de S3](https://aws.amazon.com/s3/pricing/)
para la región y volumen del proyecto antes de activar el entorno real.

Referencias: [seguridad de S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
y [upload_fileobj de boto3](https://docs.aws.amazon.com/boto3/latest/reference/services/s3/client/upload_fileobj.html).

## Verificación

```powershell
docker compose exec -T backend python -m unittest discover -s tests -v
docker compose exec -T frontend npm run build
docker compose exec -T frontend npm run check:interfaces
```

Las pruebas HTTP usan una base temporal y fuerzan modo local. Las pruebas
de S3 usan respuestas simuladas de botocore, sin credenciales reales ni red.
Cubren permisos, límites, archivos disfrazados, corrección, revisión obsoleta,
conservación del original, cifrado de carga, descarga y compensación de rollback.
Validar además carga y descarga contra el bucket real al configurarlo.
