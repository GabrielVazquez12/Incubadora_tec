# Boletín público

Publicado y verificado en AWS el 6 de octubre de 2026. La migración
`184ed20a6311` está aplicada en RDS y el servicio utiliza la imagen
`release-20261006-4763ece`. La verificación HTTPS confirmó permisos,
borradores ocultos, programación, caducidad y agenda pública.

La portada da prioridad al boletín de noticias, convocatorias, avisos y próximos eventos. No enlaza a demostraciones y las rutas de vista previa no están habilitadas en la aplicación pública; únicamente se habilitan expresamente en las comprobaciones de interfaces.

## Gestión de contenido

En **Coordinador → Boletín** se crean y editan publicaciones con título, resumen, contenido, categoría, fecha de publicación, fecha opcional de cierre, visibilidad y prioridad. Para retirar una publicación se desmarca **Publicar en el sitio** y se guarda. Se conserva el contenido para futuras ediciones.

La API pública `/public/newsletter` muestra solamente publicaciones marcadas para publicación, con fecha de inicio alcanzada y sin fecha de cierre vencida. La fecha de cierre se incluye completa; el contenido deja de aparecer al día siguiente. Las fechas se interpretan en horario de Ciudad de México. La portada actualiza la consulta cada cinco minutos y al recuperar el foco.

Los eventos se gestionan desde **Coordinador → Eventos** y aparecen automáticamente si están activos y su fecha/hora todavía no ha pasado. No se publican datos de asistentes o usuarios. Los cupos y la inscripción se consultan al iniciar sesión.

## Contenido inicial

La migración `184ed20a6311` incorpora tres artículos informativos sobre servicios existentes del portal, publicados el 6 de octubre de 2026 y vigentes hasta el 6 de noviembre. No anuncian talleres o convocatorias sin confirmar. Coordinación puede sustituirlos o retirarlos con el editor. No se crean eventos de ejemplo en la base de datos.

Esta sección es un boletín web; no envía correos ni ofrece una suscripción por email.

## Instalación

Aplicar `alembic upgrade head` antes de servir el frontend actualizado. La migración depende de `073dc19b5210`. Los endpoints `/admin/publications` requieren una cuenta de coordinación; el endpoint público no requiere autenticación.
