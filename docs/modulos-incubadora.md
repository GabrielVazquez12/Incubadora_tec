# Modulos de Incubadora

## Alcance verificado

Las rutas autenticadas utilizan la API y PostgreSQL. `/vista-previa` conserva
datos de demostracion; no usarla para comprobar persistencia.

| Modulo | Operaciones | Comprobacion |
|---|---|---|
| Usuarios y roles | Alta, edicion, acceso por rol, proteccion de cuenta propia y cuentas con historial | HTTP; no se permite degradar a un coordinador con tutorias confirmadas |
| Eventos e inscripciones | Catalogo, alta, edicion, desactivacion, reserva gratuita y cancelacion | HTTP; concurrencia por el ultimo lugar, permisos, precio y cupo |
| Tutorias | Disponibilidad propia, reserva, cancelacion, conclusion e historial | HTTP; bloqueo de solapamientos, horarios vencidos y coordinadores no disponibles |
| Seguimiento | Proyectos, integrantes, avances, tareas, estatus y comentarios | HTTP; aislamiento entre proyectos y persistencia |
| Registros y solicitudes | Borrador, anexos, revision, correcciones, aprobacion y conversion de externo a emprendedor | HTTP; descarga Word y permisos de revision |
| Reportes | Proyectos, emprendedores, avances, estadisticas y exportacion CSV | Datos de la API y renderizado; cuenta integrantes y especialidades fuera del catalogo inicial |
| Pagos | Consulta de movimientos y comprobantes de prueba | Pruebas locales de pago simulado y reembolso; los cobros reales siguen deshabilitados |
| Innovación | Borrador, edición, envío a revisión, observaciones, correcciones, aprobación/rechazo, etapas y exportación CSV | HTTP; propiedad, duplicados, estados desactualizados, historial y avance Local → Regional → Nacional |
| Asistencia y constancias | Confirmación/corrección de asistencia y descarga PDF por participante o coordinación | HTTP; no se emiten sin asistencia ni para otro participante; revisión visual de nombres largos |

No se afirma que exista una pasarela de pagos real. Hace falta elegir y configurar
un proveedor, validar su notificacion de pago y conciliacion antes de habilitar cobros.

## Reglas de uso

- Los horarios de eventos y tutorias corresponden a `America/Mexico_City`,
  independientemente de la zona del servidor o del navegador.
- No se puede reservar una tutoria ni inscribirse en un evento que ya comenzo.
- Cada coordinador administra sus propios bloques de disponibilidad. La agenda
  general permite a coordinacion consultar y resolver sesiones.
- Las tutorias canceladas liberan el horario; su historial impide borrar el bloque.
- Al rechazar una solicitud con registro de origen, coordinacion debe indicar el
  motivo. El registro vuelve a Correcciones solicitadas, conserva su historial y
  permite modificar respuestas. Se requiere una nueva aprobacion del registro
  antes de reenviar la solicitud; al aceptarla se crea un solo proyecto.
- Las vistas sin formularios ni ventanas abiertas se actualizan cada 30 segundos
  mientras la pestaña esta visible. El boton Actualizar datos permite consultar
  manualmente. No es una conexion de notificaciones en tiempo real.
- El inicio muestra actividades futuras y tutorias cuya hora final no ha pasado.
- La baja de una cuenta con un registro inicial conserva su historial y devuelve
  un error explicativo, igual que las demas relaciones del portal.
- Innovación admite cambios del emprendedor únicamente en Borrador o Correcciones
  solicitadas. El envío bloquea la edición hasta que coordinación solicite ajustes.
  Coordinación revisa las propuestas enviadas y debe indicar observaciones al
  solicitar correcciones o rechazar. Las propuestas aprobadas avanzan una etapa
  a la vez. La participación oficial sigue sujeta a la convocatoria institucional.
- Coordinación confirma o corrige asistencia desde Eventos → Inscripciones después
  de iniciar el evento. La inscripción debe estar confirmada. El participante
  descarga su constancia desde Mis inscripciones; coordinación también puede
  descargarla. La constancia incluye nombre, actividad, fecha, modalidad y folio,
  sin firmas ni sellos institucionales. Una corrección de asistencia impide nuevas
  descargas; no puede invalidar copias descargadas previamente.
- Una inscripción con asistencia confirmada no se cancela ni elimina. Primero
  coordinación debe corregir la asistencia si fue registrada por error.

## Verificacion reproducible

```powershell
docker compose exec -T backend python -m unittest discover -s tests -v
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
```

Las pruebas HTTP crean y eliminan una base PostgreSQL temporal. No requieren
credenciales de usuarios reales ni modifican la base de desarrollo.

La verificación local del 6 de octubre de 2026 incluye 21 pruebas de backend,
pruebas de horarios, borradores y teléfonos, 53 páginas y 49 enlaces de interfaz,
controles de propuestas y asistencia, y compilación de producción. Las constancias
PDF se renderizan y revisan con nombres normales, largos y caracteres especiales.
La revisión interactiva en navegador y la validación de estos cambios en AWS
quedan pendientes; la conexión al navegador falló durante esta sesión.

Antes de ejecutar esta versión en un entorno existente, instalar las dependencias
actualizadas del backend y ejecutar `alembic upgrade head`. La migración
`073dc19b5210` añade los campos de asistencia y conserva las inscripciones previas
sin asistencia confirmada. En Docker, reconstruir backend incorpora ReportLab.

Para comprobar el despliegue, `./scripts/verify-aws.ps1 -PortalFlow` prueba por HTTPS
cuentas temporales, registro, documentos privados, avances, tareas, eventos
gratuitos, cupos, cancelaciones, tutorias y el ciclo de rechazo, correccion y
admision de una solicitud externa. Tambien verifica que el servidor rechace
pagos simulados en AWS. Limpia sus registros SQL y borra logicamente sus objetos S3;
el versionado puede conservar versiones anteriores. Ejecutar deliberadamente.
