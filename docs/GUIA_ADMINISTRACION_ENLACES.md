# Administración de Enlaces Institucionales ITS

## Perfiles y compatibilidad

Los roles técnicos siguen siendo `admin` (Coordinador), `estudiante` (Emprendedor) y `externo`. Los perfiles complementarios no modifican el enum ni los registros históricos.

| Operación nueva | Asesor | Coordinador | Administrador |
| --- | --- | --- | --- |
| Consultar expediente/documentos asignados | Solo asignados actualmente | Todos los expedientes, como antes | Todos los expedientes |
| Registrar diagnóstico, asesoría o seguimiento | Solo asignados y a su cargo | Como antes | Como antes |
| Cerrar, reactivar, cambiar estado o asignar asesor | No | Sí | Sí |
| Gestionar perfiles y consultar auditoría | No | Solo durante bootstrap, mientras no exista Administrador | Sí |

Se conservan los permisos anteriores de las cuentas de coordinación sobre usuarios y módulos. La nueva separación reserva la gestión de capacidades y la consulta de auditoría al Administrador. Un coordinador sin ese perfil no puede cambiar las credenciales ni el rol técnico de un Administrador.

## Designar al primer Administrador

1. Aplicar las migraciones aditivas con el procedimiento de publicación existente, después de un respaldo verificado. No ejecutar semillas de demostración en producción.
2. Iniciar sesión con una cuenta real de coordinación. En Roles, abrir Perfiles complementarios.
3. Configurar el perfil Administrador de una cuenta administrativa real y registrar el motivo. No se crean cuentas ni correos automáticamente.
4. La cuenta modificada debe iniciar sesión de nuevo. Si fue la propia cuenta, el portal lleva a Acceso.
5. Una vez que existe un Administrador, solo dicho perfil puede gestionar capacidades y consultar auditoría. Se impide revocar al último Administrador; primero designar otro.

## Asignar y revocar asesoría

El Administrador concede el perfil Asesor a una cuenta real de Emprendedor o Externo. No cambia sus derechos anteriores sobre sus propios proyectos. Antes de promover esa cuenta al rol técnico de Coordinador, revocar el perfil Asesor; el servidor rechaza la promoción mientras lo conserve. Coordinación selecciona esa cuenta en el expediente institucional y guarda la asignación con la versión actual.

El asesor encontrará Expedientes asignados en su menú. Puede consultar diagnóstico, bitácora y documentos del expediente, y registrar atenciones realizadas con siguiente acción y fecha de revisión. La exportación PDF del diagnóstico sigue reservada al titular y a coordinación. Las descargas comprueban de nuevo la asignación y la pertenencia del documento; no hay enlaces públicos a archivos privados.

La revocación invalida las sesiones existentes y deniega nuevos accesos de asesoría. Se conservan asignaciones y atenciones históricas; antes de volver a conceder el perfil, revisar las asignaciones conservadas. No se amplían los permisos de edición de documentos, estados, cierres, hitos o capacidades.

## Auditoría

Roles → Auditoría muestra cambios autenticados que pasan por las entidades ORM: fecha, actor, entidad, identificador, operación y nombres de campos. La inserción comparte la transacción del cambio; si se revierte, también se revierte la entrada de auditoría. Se registran cambios de credenciales sin copiar sus valores.

No contiene valores de formularios, contraseñas, hashes, tokens, contenido de archivos ni copias del texto enviado. Los historiales funcionales existentes continúan con sus reglas anteriores. Las escrituras públicas conservan sus evidencias funcionales; este registro general se limita a operaciones autenticadas. No representa una auditoría de lecturas ni un mecanismo de inmutabilidad frente a acceso SQL directo de infraestructura.

No hay endpoints para editar o borrar auditoría; el ORM también bloquea esos cambios. La política institucional de conservación y el control de acceso directo a la base deben definirse operacionalmente; no se ejecuta purga automática.

## SEO, privacidad y calidad

`frontend/public/site-pages.json` es la fuente de títulos y descripciones de páginas públicas. React actualiza la metadata al navegar y el servidor la incluye en el HTML inicial. Las páginas privadas y capturas no tienen indexación; robots/sitemap solo descubren rutas públicas informativas. No sustituyen los permisos backend.

El servidor existente devuelve 403/404 con la aplicación accesible y metadata sin indexación. Los assets compilados con hash usan caché larga; la aplicación se revalida, los datos privados mantienen `no-store` y el servidor aplica compresión, `nosniff`, política de referente y denegación de frames.

La URL canónica y el sitemap usan el origen de la petición. Verificar el origen HTTPS recibido detrás del proxy al publicar. No se inventa un dominio institucional.

## Rollback

Las migraciones E/F solo agregan tablas. Si contienen datos, sus downgrades se bloquean. Revertir la imagen de aplicación conservando tablas, perfiles, auditoría y documentos. Mantener los cambios de versión de sesión y solicitar nuevo acceso si corresponde. Una versión anterior no interpreta los perfiles complementarios: revisar el retorno a los permisos técnicos anteriores antes de revertir. Nunca borrar datos para forzar un downgrade.

Continúan pendientes los contenidos institucionales reales: aviso aprobado, contactos/redes, convocatoria/manual, fechas/sedes y criterios de operación. La publicación requiere los preflights y respaldo del procedimiento existente.
