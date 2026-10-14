# Fase D: encuestas

Constructor y respuestas conectados a PostgreSQL; ninguna respuesta ficticia se precarga. Las referencias del diagnóstico de 25 respuestas se publican por separado como contenido histórico proporcionado.

## Funcionalidad y archivos

- `backend/app/models/encuestas.py`: encuesta, preguntas y respuestas; FK y unicidad por encuesta/identidad.
- `schemas/encuestas.py`: tipos JSON estrictos, cuatro tipos de pregunta, opciones sin duplicados, rango de escala, obligatoriedad, fechas reales y límites.
- `modules/encuestas/routes.py`: administración, plantillas borrador, consulta pública, respuesta y resultados. JWT existente para coordinación/respuestas identificadas; cookie firmada HttpOnly/SameSite para respuestas anónimas. No conserva nombre, correo o IP en respuestas anónimas. No expone identidad interna en resultados/exportación.
- Migración `0c7df40d5311`, posterior a `f65ba0b2ad71`: tres tablas nuevas. Downgrade rechaza cualquier dato nuevo, evitando pérdida de respuestas.
- `frontend/src/modules/encuestas/Surveys.jsx` y `surveys.css`: constructor, lista/respuesta pública, resultados con barras/dona y CSV. Estado de envío, errores, conservación de captura y doble envío protegido.
- `App.jsx`: `/encuestas`, `/encuestas/:id`, `/admin/encuestas` y opciones existentes de coordinación. `CommunityNewsletter.jsx`: enlace desde Boletín. No se agregan tarjetas a las bienvenidas.
- `request_safety.py`: límite de 1 MB exclusivamente para encuestas, compatible con 40 preguntas acotadas y texto Unicode; el resto conserva límites previos.
- Pruebas `test_portal.py`, `encuestas-browser.cjs` y switch `-Encuestas` en runner local.

## Reglas

Publicar requiere apertura/cierre coherentes. Una encuesta identificada requiere aviso institucional aprobado y aceptación; la identidad proviene del token, nunca del request. Público objetivo es una etiqueta de audiencia, no un rol técnico inventado.

Una vez que existe una respuesta, el servidor impide modificar preguntas, público o anonimato; el constructor lo refleja. Los cambios sensibles conservan autor/fecha/configuración anterior en historial. Preguntas retiradas antes de recibir respuestas se conservan inactivas, sin borrar registros.

Reintentos con mismo folio/respuestas devuelven confirmación; un segundo folio para la misma identidad devuelve 409. El cookie anónimo protege ese navegador, no verifica personas únicas si borran cookies o cambian dispositivo; ese límite es explícito. La consulta utiliza `no-store` para no compartir estado personal del cookie.

Los resultados cuentan respuestas reales. Preguntas opcionales no contestadas se excluyen del denominador; multiselección puede sumar más de 100%. CSV reutiliza la protección existente contra fórmulas de hojas de cálculo.

## Verificación

- `npm test --prefix frontend`: aprobado, incluyendo rutas/roles/bienvenida anterior.
- `npm run build --prefix frontend`: aprobado; 162 módulos, JS 465.09 kB (140.52 kB gzip).
- Suite completa `python -m unittest discover -s tests -v`: 38 pruebas aprobadas en 182.853 s, sin omisiones.
- Prueba HTTP focalizada: permisos, cookies, tipos, duplicados concurrentes, consentimiento, bloqueo de edición y resultados aprobados.
- `./scripts/verify-design-local.ps1 -Port 8091 -Encuestas`: aprobado. Chrome real: cabecera/menús y formularios anteriores, constructor de cuatro tipos, cookie anónimo, doble envío, confirmación tras recarga, gráficos y móvil/escritorio.

## Uso

1. Coordinador → Encuestas: crear una o cargar propuestas borrador para alumnos, docentes y usuarios de la Incubadora.
2. Completar preguntas/opciones, obligatoriedad, apertura/cierre, modo de respuesta; publicar. Para modo identificado, configurar antes aviso aprobado desde Catálogo.
3. Abrir vista pública y responder. Repetir envío/recarga debe conservar una sola respuesta.
4. Encuestas → Resultados: revisar conteos, porcentajes, texto y CSV. Intentar editar preguntas tras recibir respuestas debe rechazarse; crear nueva encuesta si cambia el diseño.

## Pendientes

Revisión institucional de preguntas, aviso y calendario; posibles controles adicionales contra abuso distribuido si aumenta el tráfico. No hay verificación absoluta de persona única en anonimato, ni envío automático de invitaciones. AWS conserva la fase A hasta el despliegue conjunto con backup y migraciones aditivas.
