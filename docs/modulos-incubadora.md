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

No se afirma que exista una pasarela de pagos real. Hace falta elegir y configurar
un proveedor, validar su notificacion de pago y conciliacion antes de habilitar cobros.

## Reglas de uso

- Los horarios de eventos y tutorias corresponden a `America/Mexico_City`,
  independientemente de la zona del servidor o del navegador.
- No se puede reservar una tutoria ni inscribirse en un evento que ya comenzo.
- Cada coordinador administra sus propios bloques de disponibilidad. La agenda
  general permite a coordinacion consultar y resolver sesiones.
- Las tutorias canceladas liberan el horario; su historial impide borrar el bloque.
- Las vistas sin formularios ni ventanas abiertas se actualizan cada 30 segundos
  mientras la pestaña esta visible. El boton Actualizar datos permite consultar
  manualmente. No es una conexion de notificaciones en tiempo real.
- El inicio muestra actividades futuras y tutorias cuya hora final no ha pasado.
- La baja de una cuenta con un registro inicial conserva su historial y devuelve
  un error explicativo, igual que las demas relaciones del portal.

## Verificacion reproducible

```powershell
docker compose exec -T backend python -m unittest discover -s tests -v
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
```

Las pruebas HTTP crean y eliminan una base PostgreSQL temporal. No requieren
credenciales de usuarios reales ni modifican la base de desarrollo.

Resultado local: 18 pruebas de backend aprobadas, pruebas de horarios, borradores
y telefonos aprobadas, 53 paginas y 49 enlaces de interfaz comprobados y compilacion
de produccion correcta. La revision visual interactiva queda pendiente: no habia
un navegador conectado en la sesion de trabajo.

Para comprobar el despliegue, `./scripts/verify-aws.ps1 -PortalFlow` prueba por HTTPS
cuentas temporales, registro, documentos privados, avances, tareas, eventos
gratuitos, cupos, cancelaciones y tutorias. Tambien verifica que el servidor rechace
pagos simulados en AWS. Limpia sus registros SQL y borra logicamente sus objetos S3;
el versionado puede conservar versiones anteriores. Ejecutar deliberadamente.
