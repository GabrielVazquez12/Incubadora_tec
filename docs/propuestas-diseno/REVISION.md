# Revisión de las propuestas

Se aplicaron frontend-design y web-design-guidelines a los archivos de este directorio. La composición se contrastó con la identidad oficial y las capturas de escritorio/móvil. Las verificaciones automáticas no constituyen una certificación de accesibilidad.

## editorial.html

✓ pass: identidad sin alteraciones, orden de encabezados, enlace de salto antes de la barra de revisión, imágenes con dimensiones, navegación semántica y controles de teclado. Lighthouse accesibilidad 100 / buenas prácticas 100.

## innovacion.html

✓ pass: mapa como grupo de enlaces con destino real, iconos decorativos ocultos de tecnologías de asistencia, imágenes con dimensiones y menú móvil comprobado. Lighthouse accesibilidad 100 / buenas prácticas 100.

## index.html y comparador.js

✓ pass: botones nativos con estado aria-pressed, iframe con título, selección reflejada en URL, escala de presentación separada del ancho real simulado, sin desbordamiento en 1440/390/320 px.

## propuestas.css y portadas.js

✓ pass: fuentes locales con swap, despeje proporcional de la imagen completa, foco visible, adaptación móvil, ausencia de movimiento automático y respeto a movimiento reducido. Escape cierra el menú y devuelve el foco al control.

Se corrigieron durante la revisión el orden inicial del enlace de salto y la legibilidad de las etiquetas del mapa. El navegador verificó finalmente 9 escenarios sin errores JavaScript. Al integrar en React hay que volver a evaluar la aplicación completa y su rendimiento, sin trasladar automáticamente estas puntuaciones a producción.


Ampliación A (14 octubre 2026): Newsletter con contenido público real fechado, filtros y búsqueda; propósito institucional con fuente; contacto telefónico y ubicación del campus con enlaces oficiales. Chrome: 9 escenarios y pruebas de contenido aprobados. Capturas A actualizadas. No se repitió Lighthouse; sus puntuaciones previas corresponden al diseño inicial. Integración React pendiente; conservar Newsletter dinámico existente.
