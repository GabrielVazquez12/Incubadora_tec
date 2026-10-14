# Publicación conjunta de fases B–F

## Plan

1. Confirmar cuenta, servicio anterior y versión de base. Conservar imagen anterior y cambios de infraestructura existentes.
2. Crear snapshot RDS y esperar disponibilidad. Intentar restaurarlo en una instancia privada temporal con la misma red y parámetros. Si la cuota de la cuenta lo impide, realizar copia lógica cifrada en el bucket privado existente, descargarla dentro de una tarea aislada de ECS, verificar su SHA-256, restaurarla en PostgreSQL temporal y ensayar allí las migraciones sin copiar datos a equipos locales. Registrar explícitamente que la restauración de snapshot RDS no pudo probarse.
3. Identificar el código mediante commit, construir la imagen Linux, publicarla con etiqueta inmutable y comprobar digest y escaneo ECR.
4. Ejecutar preflight sobre la base real y preparar un change set con la plantilla anterior: solo ImageTag, servicio sin reemplazo y nueva revisión de MigrationTask. No cambiar RDS, S3, IAM ni red de producción.
5. Solo con respaldo, restauración y ensayo aprobados: aplicar migraciones aditivas hasta `637ddccf1603`, verificar conservación de tablas anteriores y publicar el change set validado.
6. Esperar estabilidad, verificar HTTPS, metadata, rutas y permisos; retirar únicamente recursos temporales propios. Conservar snapshot y evidencias locales sin secretos.

## Estado

Preparación iniciada el 14 de octubre de 2026. Estado real inicial: CloudFormation UPDATE_COMPLETE, servicio ECS activo en revisión 12, imagen `enlaces-fase-a-61f0d35`; RDS disponible. La sesión AWS se renovó. Código `ea2d990` publicado en `destino/feat/enlaces-institucionales-its`. Imagen `enlaces-bf-ea2d990`, índice `sha256:ab991535ad732b622ff27881acc5e1ff095c11484a5bd014193a5fe199636d07`; manifiesto Linux `sha256:f34bbcd14f0158e3f96c996d0aede336a6302ac8dc91d7fc960a48a7483bd6b2`.

Snapshot `incubadora-enlaces-bf-20261014112430` disponible al 100 %. Preflight ECS `069d516ee75e476cba9c791c506ff824`: código 0, esquema inicial `3a608b5c8533`, todas las incompatibilidades en cero.

Change set `enlaces-bf-ea2d990` creado y validado: Service sin reemplazo y nueva revisión de MigrationTask; no cambia la infraestructura de datos. Escaneo Linux COMPLETE: 0 críticos, 5 altos, 10 medios, 3 bajos; mismas cantidades de hallazgos pendientes de la fase A.

AWS rechazó la segunda instancia con `InstanceQuotaExceeded`: límite de instancias del plan gratuito. No se cambió el plan ni se detuvo la base activa. Se prepara ensayo lógico en una tarea aislada con PostgreSQL 17; la fuente RDS permanece en PostgreSQL 15.19. No equivale a probar la restauración física del snapshot ni una restauración lógica en PostgreSQL 15.

Los resultados finales se registrarán aquí; este estado todavía no declara completado el despliegue.

## Conservación y reversión

Las migraciones añaden las tablas B–F sin borrar datos existentes. Ante un fallo, mantener la imagen anterior y el esquema ampliado; no ejecutar downgrade en producción ni eliminar datos para permitirlo. La restauración de respaldo se prueba en otra instancia privada; nunca sobrescribe la instancia activa. La copia temporal genera cargos mientras exista y se retirará tras las comprobaciones.


## Ajuste de metadata durante la aceptación

La primera publicación completó CloudFormation y ECS, pero la comprobación real detectó sitemap/canónicos con http detrás del balanceador HTTPS. La versión instalada de Uvicorn acepta IPs exactas, sin CIDR. Se añadió `public_origin` limitado a metadata: confía en `X-Forwarded-Proto` solo para http/https y conexiones desde las subredes configuradas del balanceador. La plantilla documenta esas redes; no se modifican permisos ni el tratamiento de IPs de autenticación. Build aprobado y 45 pruebas backend aprobadas en 136,663 s, incluyendo fuentes no confiables, cabecera inválida y ausencia de configuración. Se prepara una segunda revisión de aplicación, sin nuevas migraciones.
