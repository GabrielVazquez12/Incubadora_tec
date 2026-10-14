# Fase F completada y verificada

Perfiles complementarios, asesoría asignada, auditoría, SEO y optimización de carga implementados. Informe: `docs/FASE_F_ENLACES.md`. Operación: `docs/GUIA_ADMINISTRACION_ENLACES.md`.

- Backend: 44 pruebas aprobadas en 95,576 s.
- Frontend: pruebas de 56 páginas y 78 enlaces, build y regresión completa de Chrome aprobados.
- Lighthouse local: rendimiento móvil 93 y escritorio 100; accesibilidad, buenas prácticas y SEO 100 en ambos.
- Artefactos finales: `.local/design-test-cff003fffc304cf5a420d2838d9fbef3`.
- Sin commits, push, cambios AWS ni migraciones de producción en esta reanudación. Los cambios permanecen en el worktree.
- Siguiente etapa: preparar la publicación conjunta con respaldo y comprobaciones previas; el despliegue y los datos institucionales reales siguen pendientes. Los apartados siguientes son históricos.

---

# Reanudación completada — fase E

El usuario solicitó reanudar. La integración de fase E está implementada y verificada; el texto de pausa que sigue se conserva como referencia histórica.

- Informe actual: `docs/FASE_E_ENLACES.md`.
- Backend: 41 pruebas aprobadas, migración y conservación de datos verificadas.
- Frontend: pruebas y build aprobados. Chrome aprobó regresiones anteriores y el recorrido final de difusión en escritorio/320 px.
- Capturas finales E: `.local/design-test-8ac52138044e4b8db8b44a73ae879697`. Regresiones B/C/D y navegación: `.local/design-test-abfb3efe170540ef923400c07b628467`.
- Se corrigieron el texto omitido de plantillas/envíos, el reinicio de nuevos registros y la navegación de listado a detalle de eventos; el runner de Chrome ahora tiene límites de espera.
- Los cambios siguen sin commit. En esta reanudación no se hicieron commits, push ni despliegues. No se aplicaron migraciones de producción.
- Siguiente trabajo: fase F del plan original y posteriormente despliegue conjunto. Mantener pendientes los datos institucionales reales descritos abajo.

---

# Punto de reanudación — pausa solicitada el 14 de octubre de 2026

El usuario pidió pausar y continuar en su siguiente sesión. No iniciar nuevas pruebas, commits ni despliegues hasta que solicite reanudar. Los cambios no confirmados se conservan en el worktree.

## Repositorio y publicación

- Worktree correcto: `C:\proyectos\IncubadoraEnLinea\incubadora-tec-audit` (el directorio padre corresponde a otro proyecto anterior).
- Rama: `feat/enlaces-institucionales-its`.
- Remote correcto: `destino`, `https://github.com/Kike1196/Incubadora_tec.git`. No usar `origin` para publicar: apunta al repositorio anterior.
- B: `a8d0ebf` y `7893b1b`, publicados.
- C: `b9fb21c` y `c9bba59`, publicados.
- D: `5199af1` y `b7e792c`, publicados (push confirmado).
- AWS todavía ejecuta **fase A**, revisión ECS 12; no se han ejecutado migraciones B/C/D/E ni se han desplegado esas fases. La autorización previa de commit/push/despliegue permanece, pero el trabajo está pausado.

## Verificado antes de la pausa

- B: 34 pruebas backend, frontend/build y Chrome completo; diploma PDF de una página renderizado y revisado.
- C: 37 pruebas completas, cuatro pruebas finales de migración/reglas/HTTP, frontend/build y Chrome con continuidad InnovaTec–Incubadora y captura pública simplificada. PDF largo revisado, dos páginas.
- D: 38 pruebas backend completas; frontend/build; Chrome completo de marca/menús/formularios anteriores y constructor, cuatro tipos, anonimato, doble envío, persistencia y resultados en móvil/escritorio.
- Después de D se corrigió la legibilidad de tablas móviles con desplazamiento horizontal contenido en `surveys.css` e `incubation.css`. Build y `git diff --check` pasaron. Esas dos correcciones aún no tienen commit; revisar sus capturas en la siguiente regresión.

## Fase E en curso — sin commit ni verificación funcional completa

Plan: `docs/PLAN_FASE_E.md`. Archivos nuevos:

- `backend/app/models/enlaces.py`: piezas, visitas, plantillas, envíos manuales, FAQ, configuración/contacto y fichas de eventos.
- `backend/app/schemas/enlaces.py`: DTOs estrictos y enlaces validados.
- `backend/app/modules/difusion/routes.py`: APIs privadas/públicas; reutiliza noticias, Evento, galería e inscripciones.
- `backend/alembic/versions/526ccbbe0502_difusion_vinculacion_y_fichas_de_.py`: ocho tablas aditivas, guard de downgrade sin datos.
- `frontend/src/modules/difusion/Outreach.jsx` y `outreach.css`: pantallas implementadas, **aún no integradas en App/menús/FAQ/pie/Inicio**.
- Integraciones backend en `main.py`, `models/__init__.py` y límite anónimo en `auth/rate_limit.py`.

Las rutas específicas GET se registraron antes de la colección genérica para evitar interceptar configuración/envíos/contactos. El contacto bloquea la fila de privacidad para serializar reintentos; no envía correo. Las tres fichas iniciales son borradores con fechas/lugar pendientes, sin crear eventos operativos ficticios. Noticias borrador/futuras/caducadas no se exponen a través de difusión.

Próximos pasos al reanudar:

1. Recuperar resultado del comando de migración/comparación temporal pendiente (sesión de shell `56456`, si sigue disponible); no asumir que E esté verificada.
2. Revisar/integrar `Outreach.jsx` en rutas, submenús existentes, preguntas frecuentes de Incubadora/InnovaTec, contactos del pie, enlaces de Inicio y detalle público de eventos. Usar solo datos configurados; no fabricar contactos, redes, fechas o URLs institucionales.
3. Añadir pruebas de permisos, tipos, privacidad, contacto concurrente, versiones, visibilidad de noticias, plantillas/envíos y eventos. Ejecutar frontend/build/backend y Chrome; documentar y commitear E solo en verde.
4. F: asesor/administrador mediante extensión compatible, auditoría, SEO/sitemap/robots, accesibilidad, rendimiento/Lighthouse y documentación. Sin dependencias nuevas injustificadas ni reescritura de arquitectura.
5. Despliegue conjunto AWS tras backup, preflight y migraciones aditivas. Rollback conserva datos; nunca ejecutar downgrade destructivo en producción.

## Recursos y datos pendientes

Contenedor propio `incubadora-tec-audit-db` conserva PostgreSQL de pruebas. Base temporal nombrada en `.local/phase-b-db.txt`, patrón `test_innovatec_<32hex>`. Los runners de Chrome eliminan sus contenedores/bases/cuentas al finalizar. No tocar contenedores ajenos `bycode-web-1` o `bycode-backend-1`.

Imagen local `incubadora-tec-audit:phase-a` tiene código **D** pese a su nombre histórico; no asumir que representa la imagen A de AWS. Imagen `incubadora-tec-audit:pdf-qa` solo para Poppler, nunca desplegarla.

Faltan convocatoria/manual oficiales, aviso aprobado real, fechas/sedes, contactos/redes, validación de catálogo/hitos, umbral de inactividad institucional y URL externa InnovaTecNM. No hay respuestas, participación o mensajes reales precargados. La confirmación de capturas usa la cuenta existente; no se recibió respuesta que autorice captura completamente anónima.

Informes de fases: `FASE_A_ENLACES.md`, `FASE_B_ENLACES.md`, `FASE_C_ENLACES.md`, `FASE_D_ENLACES.md`. Las capturas y PDFs sintéticos están en `.local/`, ignorados por Git. Antes de la pausa, la última regresión D guardó capturas en `.local/design-test-7441a6bb0dd347c0b0d0da7e6d030916`.
