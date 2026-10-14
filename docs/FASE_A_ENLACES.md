# Fase A — Identidad y navegación de Enlaces Institucionales ITS

## Alcance realizado

Fase A aprobada después de la auditoría. Se aplicó la excepción compacta de margen del encabezado de 12 px en escritorio y 8 px en móvil. Las fases B–F no están implementadas: sus entradas nuevas muestran marcadores explícitos de configuración pendiente y no simulan capturas, resultados o envíos.

Rama: `feat/enlaces-institucionales-its`, en el repositorio `Kike1196/Incubadora_tec`. Se conservan JavaScript/React/Vite, FastAPI/Pydantic, SQLAlchemy/Alembic y PostgreSQL. No se instalaron dependencias nuevas.

## Cambios por funcionalidad

| Funcionalidad | Archivos creados o modificados |
| --- | --- |
| Activos oficiales y tipografía | `frontend/public/brand/enlaces-*`, README de marca; `frontend/public/fonts/*` y licencias OFL; `shared/BrandImage.jsx`, `shared/InstitutionalBrand.jsx`, `shared/design/{tokens,brand}.css`, Tailwind |
| Menú por actor y bienvenida | `shared/design/Navigation.jsx`, `navigation.css`, `Icon.jsx`, `layout.css`, `PendingModule.jsx`; `shared/portal/{Home,PortalLayout}.jsx`; `App.jsx`; `InstitutionalFooter.jsx`; pruebas `interface-checks.jsx` |
| Inicio público y páginas informativas | `modules/publico/{Landing,PublicLayout,PublicPages,Newsletter}.jsx`, `landing.css`, `newsletter.css`, `shared/design/public.css`, `index.html` |
| Acceso y registro | `modules/autenticacion/{Login,Registro,RutaProtegida}.jsx`; se conservan handlers de autenticación y campos/IDs/DTOs |
| Componentes y tema compartidos | `shared/portal/ui.jsx`: stepper horizontal/vertical y skeleton; botones, paneles, campos, tablas, badges, modales, CSV y barras existentes reutilizados; estilos existentes referencian la paleta central mediante aliases |
| Verificación y documentación | `frontend/scripts/{design-browser.cjs,design-tokens.test.mjs,browser-helper.cjs,interface-checks.jsx}`, `frontend/package.json` solo scripts; `scripts/verify-design-local.ps1`; README; auditoría inicial y este documento; capturas |

Los paths bajo `shared`/`modules` corresponden a `frontend/src`. No se renombraron, movieron ni borraron archivos existentes. Los estilos de tarjetas se conservan porque Externo e inicio interno InnovaTec aún los utilizan.

## Identidad oficial

- Original JPEG 1254 × 1254 preservado, copia verificada por SHA-256. Variantes completas 1200/800/400 en WebP y JPEG. La composición no se recortó para el hero, acceso, bienvenida o pie.
- Recorte rectangular del símbolo central `(280,220,1010,676)`: 730 × 456. Variantes proporcionalmente reducidas para 48/96/144 px de alto y favicon derivado, sin redibujo/recolor/filtros/sombras. El encabezado utiliza srcset por ancho y tamaños reales de 77/64 px.
- `InstitutionalBrand` muestra el símbolo y texto HTML real ENLACES / INSTITUCIONALES ITS; en móvil solo ENLACES. No muestra los escudos antiguos por separado.
- `BrandImage` comparte el alt exacto solicitado, fuentes responsivas, dimensiones explícitas, carga prioritaria en hero/acceso/bienvenida y diferida en pie. Su marco mantiene un despeje proporcional al ancho del símbolo central; por eso la imagen completa se reduce en móviles.
- Fuentes autoalojadas Montserrat y Cormorant Garamond normal/italic, pesos variables 400–700, `font-display: swap`, fallbacks y licencias. Total WOFF2 114856 bytes; sin llamadas a Google durante el uso.
- Paleta central muestreada de la imagen, con guinda #700020, plata decorativa, texto #2B2B2E, azul puntual #183050 y fondo #F7F5F2. Los alias de colores de estilos anteriores se resuelven a la nueva paleta.

## Pantallas y navegación

**Inicio público, escritorio:** encabezado en dos franjas sticky, lockup compacto a la izquierda y acceso a la derecha; menú Inicio/Incubadora/InnovaTec/Vinculación/Eventos/Contacto. Hero con imagen oficial a la izquierda y texto/lema/registro a la derecha. Cuatro pilares, dos programas, cinco ejes, noticias/eventos desde la API existente, proceso de acceso y cierre «¡Tu idea, nuestro apoyo!». Pie con marca completa y contactos/redes pendientes explícitos.

**Inicio público, móvil:** franja de identidad de 56 px y botón de menú; imagen completa sobre el texto; pilares en dos columnas con icono sobre etiqueta; programas, ejes y proceso en una columna. Menú dialog nativo con todas las opciones, foco dentro, Escape y devolución de foco. Comprobado a 320 px.

**Acceso/registro:** imagen completa y lema a la izquierda del formulario en escritorio; en móvil se apilan. Campos, IDs, validación, estados de envío, conservación de datos, llamadas a `/auth/login` y `/auth/registro`, almacenamiento JWT y redirección por rol permanecen.

**Coordinador/Emprendedor:** bienvenida centrada «Bienvenido(a), [nombre]», rol, imagen completa de hasta 420 px y lema. Sin módulos, estadísticas, boletín compacto, widgets ni enlaces de acceso en su cuerpo. Actualizar datos continúa disponible como operación existente. Pie sin navegación de módulos.

**Menú de Coordinador:** Inicio, Boletín, Usuarios, Roles, Eventos, Gestionar noticias, Pagos, Reportes, Tutorías, Seguimiento, Solicitudes y Registros conservan nombres, orden y destinos. Nuevas entradas Encuestas/Catálogo/Gestión InnovaTec; Difusión dentro de Gestionar noticias, Inactivos dentro de Seguimiento, Indicadores dentro de Reportes. Las entradas pendientes están protegidas por la ruta de coordinador, pero no tienen backend nuevo ni operaciones habilitadas todavía.

**Menú de Emprendedor:** Inicio, Boletín, Proyectos, Mis avances, Eventos, Tutorías, Mis pagos y Mis inscripciones conservados; sin opciones administrativas nuevas. Ambos conservan el destino original de InnovaTecNM `/innovatecnm/inicio`, que realmente es interno. La descripción accesible lo indica; no se inventó una URL externa ni target diferente.

Externo conserva sus tarjetas, rutas y permisos; el inicio interno de InnovaTec conserva su catálogo. Todos los destinos antiguos de las 14 tarjetas siguen funcionando. La tarjeta Boletín de Coordinador correspondía a Gestionar noticias, no al Boletín de lectura; se conservan las dos rutas.

## Pruebas y evidencia

| Comando/comprobación | Resultado |
| --- | --- |
| `npm test --prefix frontend` | Aprobado; incluye contrastes AA, agenda, drafts, teléfono/UTF-8, catálogos y 56 páginas/74 enlaces, rutas, identidad y permisos |
| `npm run build --prefix frontend` | Aprobado; Vite, 152 módulos; compilación de producción con `VITE_API_URL=/api` |
| `node frontend/scripts/design-browser.cjs` | Aprobado en Chrome real: 320 px sin overflow, alturas 72/56, scroll sticky, 14 destinos, roles, submenús por teclado, Escape/foco, imágenes 3× y login real |
| `npm run test:browser --prefix frontend` | Aprobado: registro, Unicode, límite bcrypt, doble envío, error de login, borrador parcial y refresh fallido después de guardar |
| `./scripts/verify-design-local.ps1 -Port 8091 -SkipBuild` | Aprobado con red/BD propias, imagen real y cuentas sintéticas; limpieza de contenedores/red y archivo de credenciales |
| `python -m unittest discover -s tests -v` dentro de imagen final y PostgreSQL aislado | 33 aprobadas, sin skips; 211.725 segundos; migraciones, integridad, CRUD, roles/IDOR, archivos, revisiones/estados, constancias y Word |
| `git diff --check`, `node --check`, parser PowerShell | Aprobados |
| Lint/formatter/typecheck/Lighthouse | No configurados o no ejecutados; no se inventa un resultado. Contraste de tokens verificado; esto no certifica por sí solo toda la accesibilidad AA ni Lighthouse ≥90 |

Durante la prueba se corrigieron dos desbordamientos: ancho mínimo de los pilares a 320 px y texto para lector de pantalla que escapaba de la barra desplazable (ahora aria-label). El helper CDP se corrigió para emitir Enter y esperar el documento nuevo al recargar la misma URL. La prueba local se compiló con `/api` después de detectar que una copia de desarrollo intentaba conectar a localhost:8000. Ningún fallo se omitió ni se trató como éxito.

### Capturas

Las capturas usan cuentas y BD sintéticas; no representan usuarios, métricas o registros institucionales reales. Móvil significa viewport 320 px en Chrome, con densidad 3×; no una certificación de todos los dispositivos/navegadores.

- Inicio: [escritorio](capturas-fase-a/inicio-escritorio.png), [móvil](capturas-fase-a/inicio-movil.png).
- Acceso: [escritorio](capturas-fase-a/acceso-escritorio.png), [móvil](capturas-fase-a/acceso-movil.png).
- Coordinador: [escritorio](capturas-fase-a/coordinador-escritorio.png), [móvil](capturas-fase-a/coordinador-movil.png), [menú móvil](capturas-fase-a/coordinador-menu-movil.png), [submenú](capturas-fase-a/coordinador-submenu-escritorio.png).
- Emprendedor: [escritorio](capturas-fase-a/emprendedor-escritorio.png), [móvil](capturas-fase-a/emprendedor-movil.png), [menú móvil](capturas-fase-a/emprendedor-menu-movil.png).

## Cómo probar y administrar

1. Instalar/iniciar con los comandos y variables existentes del README. No usar credenciales demo en producción. Aplicar únicamente las migraciones existentes para un entorno nuevo; esta fase no agrega migraciones.
2. Visitar `/`, abrir las seis opciones públicas, comprobar los dos programas y el contenido real del boletín. Los marcadores señalan información pendiente, no formularios operativos nuevos.
3. Iniciar sesión como Coordinador/Emprendedor: comprobar bienvenida y las opciones originales. Abrir URLs antiguas directamente, proyectos/avances, eventos, tutorías, pagos/inscripciones y revisión de registros según rol.
4. A 320 px, abrir el menú con teclado o botón; comprobar todas las opciones, usuario y cerrar sesión. Escape vuelve al botón. En escritorio, desplegar Reportes con ArrowDown y cerrar con Escape; el foco vuelve al control.
5. Noticias siguen administrándose desde Gestionar noticias: creación/edición, borrador/publicación y vigencia existentes. Eventos/galerías/asistencia y constancias siguen en sus módulos actuales. No usar los marcadores de Encuestas/Catálogo/Difusión/Gestión InnovaTec como gestión ya habilitada.
6. Para una prueba automatizada aislada: `./scripts/verify-design-local.ps1`; crea infraestructura local temporal, prueba diseño/formularios, conserva screenshots y limpia sus propios recursos. Requiere Docker Desktop, Node y Chrome. No requiere credenciales AWS.

## Compatibilidad y pendientes

No se modificó código de backend, firmas de sus funciones, endpoints/DTOs/modelos existentes, tablas/columnas/roles ni permisos. No se modificó `.env`. No se eliminaron archivos. Los roles siguen siendo admin=Coordinador, estudiante=Emprendedor y externo=Externo. La eliminación de las tarjetas es exclusivamente visual.

Pendientes de B–F: equipos/documentación/logística/diplomas y operación de convocatoria; diagnóstico nuevo/bitácora/seguimiento/hitos/inactivos/cierre; encuestas; difusión/visitas/envíos/contacto; perfiles Asesor/Administrador y auditoría general; SEO por ruta y metadatos sociales absolutos del servidor; privacidad institucional aprobada, Lighthouse y revisión completa de accesibilidad. Las etiquetas OG/Twitter actuales ya apuntan a la imagen completa, pero no se afirma una prueba de compartición en redes ni SEO SSR final.

Marcadores: contacto/redes/horarios, acciones de Vinculación, aviso aprobado, convocatoria/manual/requisitos/fechas/sedes, configuración de módulos nuevos, servicios/resultados/hitos. Su inventario y las decisiones abiertas están en la auditoría inicial. Antes de captura pública nueva falta confirmar si la cuenta será obligatoria para confirmar; antes de cambiar el enlace InnovaTecNM falta su URL oficial.

Despliegue de Fase A: resultados pendientes de registrar al concluir la publicación autorizada. No requiere migración de RDS.
