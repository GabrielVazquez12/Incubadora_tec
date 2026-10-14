# Publicación conjunta de fases B–F

## Plan

1. Confirmar cuenta, servicio anterior y versión de base. Conservar imagen anterior y cambios de infraestructura existentes.
2. Crear snapshot RDS y esperar disponibilidad. Restaurarlo en una instancia privada temporal con la misma red y parámetros; comprobar lectura y ensayar las migraciones allí sin copiar datos a equipos locales.
3. Identificar el código mediante commit, construir la imagen Linux, publicarla con etiqueta inmutable y comprobar digest y escaneo ECR.
4. Ejecutar preflight sobre la base real y preparar un change set con la plantilla anterior: solo ImageTag, servicio sin reemplazo y nueva revisión de MigrationTask. No cambiar RDS, S3, IAM ni red de producción.
5. Solo con respaldo, restauración y ensayo aprobados: aplicar migraciones aditivas hasta `637ddccf1603`, verificar conservación de tablas anteriores y publicar el change set validado.
6. Esperar estabilidad, verificar HTTPS, metadata, rutas y permisos; retirar únicamente recursos temporales propios. Conservar snapshot y evidencias locales sin secretos.

## Estado

Preparación iniciada el 14 de octubre de 2026. Estado real inicial: CloudFormation UPDATE_COMPLETE, servicio ECS activo en revisión 12, imagen `enlaces-fase-a-61f0d35`; RDS disponible. La sesión AWS se renovó. Los resultados finales se registrarán aquí; este plan no declara completado el despliegue.

## Conservación y reversión

Las migraciones añaden las tablas B–F sin borrar datos existentes. Ante un fallo, mantener la imagen anterior y el esquema ampliado; no ejecutar downgrade en producción ni eliminar datos para permitirlo. La restauración de respaldo se prueba en otra instancia privada; nunca sobrescribe la instancia activa. La copia temporal genera cargos mientras exista y se retirará tras las comprobaciones.
