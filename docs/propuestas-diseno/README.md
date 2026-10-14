# Propuestas visuales de Enlaces Institucionales ITS

Alcance: comparar dos portadas antes de elegir una e integrarla en React. Son documentos HTML de revisión; no cambian rutas, API, autenticación, datos ni la publicación AWS.

## Plan de diseño

Recursos comunes: marca oficial sin alteraciones, iconos existentes de `Icon.jsx`, fuentes locales Cormorant Garamond y Montserrat. Paleta: vino #700020, vino oscuro #4d0016, azul institucional #183050, plata #909090, papel #f7f5f2 y blanco #ffffff.

A, Editorial institucional: encabezado de marca y navegación actual; una portada dividida entre un gran bloque vino y una lámina blanca con la identidad completa; programas como guías de lectura, agenda y proceso. Títulos Cormorant Garamond y texto Montserrat, alineados a la izquierda. La composición tipográfica y el contraste son protagonistas.

    Marca y navegación
    [ Titular sobre vino       | Marca completa ]
    [ Cuatro accesos a pilares                  ]
    [ Incubadora: propósito y acceso             ]
    [ InnovaTec: propósito y acceso              ]
    [ Actualidad ] [ Proceso de participación    ]

B, Red de innovación: encabezado compartido; titular Montserrat y mapa navegable que conecta los cuatro pilares; programas con mayor contraste y distribución asimétrica. El mapa representa rutas reales, no indicadores ni resultados inventados.

    Marca y navegación
    [ Titular y registro      | Mapa de pilares ]
    [ Incubadora               | InnovaTec       ]
    [ Agenda y difusión                         ]
    [ Cuenta -> proyecto -> acompañamiento      ]

## Revisión del plan

Se evita una colección de tarjetas iguales y adornos sin función. El vino y las fuentes se justifican por la identidad actual del ITS; no se introduce una paleta de moda ajena a la marca. En A, las franjas y filas ayudan a escoger programa. En B, cada nodo del mapa abre su ruta real. No se inventan métricas, contactos, testimonios ni eventos. La numeración se reserva al proceso de participación, que sí es secuencial.

## Entrega

`index.html`: comparador con opciones A/B, escritorio/móvil y URL compartible para cada selección. `editorial.html` y `innovacion.html`: portadas completas. `propuestas.css`, `comparador.js` y `portadas.js`: estilos y controles sin dependencias nuevas.

Verificación: Chrome en 1440, 390 y 320 px; imágenes y fuentes locales, ausencia de desbordamiento, navegación de teclado, menú móvil, contraste y controles del comparador. Los enlaces de producto abren el portal actual en otra pestaña; los enlaces de revisión permanecen en los prototipos. No hay escrituras en producción.


## Resultado de revisión

- Chrome aprobó 9 escenarios: ambas portadas en 1440, 390 y 320 px y el comparador en esos tres anchos. Sin desbordamiento horizontal; enlace de salto, foco, menú/Enter/Escape, selector A/B y URL compartible comprobados.
- Lighthouse 13.5.0: accesibilidad 100 y buenas prácticas 100 en ambas propuestas. Informes locales: `.local/design-proposals-lighthouse-a.json` y `.local/design-proposals-lighthouse-b.json`. No se midió rendimiento de la aplicación publicada: estas portadas aún no están integradas en React.
- Capturas de escritorio, móvil y página completa revisadas visualmente en `capturas/`; `node --check` de los dos scripts y `git diff --check` aprobados. No se ejecutó la suite backend porque no hay cambios de aplicación ni de datos.
- Skills instaladas con el instalador oficial de Codex: `frontend-design` desde `anthropics/skills` y `web-design-guidelines` desde `vercel-labs/agent-skills`. Disponibles automáticamente desde el siguiente turno.

## Cómo comparar

Vista local activa: http://127.0.0.1:58082/docs/propuestas-diseno/index.html

- [A · Editorial institucional](editorial.html). [Captura escritorio](capturas/a-1440.png). [Captura móvil](capturas/a-390.png).
- [B · Red de innovación](innovacion.html). [Captura escritorio](capturas/b-1440.png). [Captura móvil](capturas/b-390.png).
- [Comparador](index.html): cambia propuesta y ancho; la URL conserva la selección.

Si el servidor local ya no está activo, desde la raíz de `incubadora-tec-audit` ejecutar `python -m http.server 8093 --bind 127.0.0.1` y abrir `http://127.0.0.1:8093/docs/propuestas-diseno/index.html`.

## Pendiente

Dirección A elegida por el usuario. Se completó su revisión visual antes de integrarla en React. Son propuestas de revisión guardadas en el repositorio local, sin commit, push ni despliegue del rediseño. La integración debe conservar rutas, controles de acceso y boletín real, y repetir la verificación de aplicación y rendimiento móvil.

## Ampliación de A · 14 de octubre de 2026

Se agregaron Newsletter visible con cinco publicaciones reales consultadas en el endpoint público del portal, búsqueda y filtros por categoría; misión y visión institucionales resumidas y vinculadas al texto oficial; contacto de Gestión Tecnológica y Vinculación; dirección del campus y enlace de indicaciones. La navegación local permite llegar a cada sección.

El Newsletter del prototipo es una copia de revisión, identificada como tal; sus enlaces abren la publicación vigente. Al integrar A en React se debe conservar el componente Newsletter existente, su API, actualización, búsqueda, filtros y lectura. No se añadió una suscripción por correo.

Fuentes consultadas:
- https://saltillo.tecnm.mx/misionyvision (misión y visión del Instituto, no del departamento).
- https://saltillo.tecnm.mx/directorio (teléfono 844 288 9460, extensión 1010). El directorio y la página de emprendimiento difieren en titulares y correos; se enlaza al directorio y se evita fijar un correo de vigencia incierta.
- https://saltillo.tecnm.mx/ (dirección del campus: Blvd. Venustiano Carranza 2400, Col. Tecnológico, C.P. 25280, Saltillo). No se encontró confirmación suficiente de otras sedes, edificio ni horario; confirmar antes de publicarlos.

Verificación actual: `node --check docs/propuestas-diseno/portadas.js`, `node .local/check-design-proposals.cjs` (9 escenarios), `node .local/check-proposal-a-content.cjs` (secciones, filtro y búsqueda sin resultados) y `git diff --check`, aprobados. Capturas de A actualizadas. Los resultados Lighthouse anteriores corresponden a la versión inicial; no se han repetido para esta ampliación. Sin cambios en React, datos de producción ni AWS.

## Integración React de A

La dirección A se integró en `frontend/src/modules/publico/Landing.jsx`, con estilos limitados a `.editorial-home` en `landing.css`. Conserva el Newsletter original conectado a su API (sin copia estática), el proceso de participación, las rutas a programas y accesos existentes. La misión y visión son síntesis institucionales con fuente; el contacto y la ubicación remiten a fuentes oficiales. No se introdujeron dependencias, cambios de backend, variables de entorno ni infraestructura.

Vista de la aplicación compilada: http://127.0.0.1:4173/ . Para la revisión local, un puente temporal de solo lectura en 127.0.0.1:8000 consulta únicamente rutas públicas del API existente, sin reenviar credenciales. No forma parte de la aplicación ni del despliegue.

Validación de integración:
- `npm test --prefix frontend`: aprobado, incluidas 56 páginas y 78 enlaces internos; conserva advertencias de Navigate en StaticRouter durante las pruebas.
- `npm run build --prefix frontend`: aprobado, 170 módulos.
- Chrome a 1440, 390 y 320 px: un h1, secciones presentes, sin desbordamiento ni errores de ejecución.
- Newsletter: cinco publicaciones reales, búsqueda sin coincidencias, restauración de resultados, apertura de noticia y cierre con Escape aprobados.
- Capturas completas de escritorio y móvil revisadas. La primera captura completa móvil agotó la espera de imágenes diferidas; la repetición con desplazamiento gradual verificó todas las imágenes cargadas y guardó la captura.
- `git diff --check`: aprobado. No hay linter, formateador ni comprobador TypeScript configurados. No se ejecutaron pruebas backend porque no se modificó. No se repitió Lighthouse para la integración.

Cambios guardados localmente, sin commit, push ni despliegue de este rediseño. Pendiente confirmar edificio, horarios y otras sedes de Vinculación antes de añadirlos.

## Publicación completada

El estado local descrito en las etapas de revisión anteriores queda actualizado: A fue integrada, guardada en el commit `224db78`, enviada al remoto `destino` y desplegada en AWS con la imagen `editorial-a-224db78`. CloudFormation UPDATE_COMPLETE y ECS revisión 16 COMPLETED. Chrome sobre producción y comprobaciones HTTP aprobados. Detalles, evidencias y reversión: [PUBLICACION_DISENO_A.md](../PUBLICACION_DISENO_A.md). El comparador conserva ambas propuestas como documentos de diseño; el portal utiliza únicamente la portada A integrada en React.
