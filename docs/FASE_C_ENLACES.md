# Fase C: registro y expediente institucional

El registro simplificado crea proyecto en revisión y diagnóstico en una transacción, confirmada con cuenta de emprendedor. El perfil puede ser alumno, docente, egresado o público externo; el rol técnico `externo` conserva Solicitud de ingreso. Se mantienen el formato anterior, su aprobación y las rutas originales para expedientes existentes.

## Funcionalidad

- `/incubadora/registro`: nombre, producto/servicio, teléfono, tipo de usuario, carrera/semestre cuando aplica, perfil, etapa, descripción, situación actual, necesidades, canal de llegada, pausa/motivo, frecuencia y modalidad. Privacidad aprobada y consentimiento versionado. Folio UUID y reintento sin duplicados.
- Diagnóstico adicional enlazado a proyecto o registro anterior, edición exclusiva del titular; PDF privado con imagen oficial completa y protección frente a texto largo.
- Expediente desde Proyectos, Mis avances y Seguimiento: diagnóstico, contacto, origen InnovaTec, bitácora de atenciones y avances anteriores, hitos, evidencias, canalizaciones e historial.
- Atención registrada únicamente con actividad, responsable real y fecha de revisión; fechas reales/coherentes, documentos del mismo proyecto, enlaces HTTP/HTTPS sin credenciales. Reintento concurrente conserva una entrada.
- Asignación a cuentas existentes de coordinación y primer contacto. El permiso independiente de asesor se integra en F. Recordatorios en pantalla, sin correo simulado.
- Próxima revisión inicial automática (7/15 días o mes calendario); cada atención registra la fecha acordada. Semana y vencidos; umbral de inactividad configurable sin valor inventado, incluyendo proyectos anteriores. Recuperación trazable de pausas/inactivos.
- Estados activo/en seguimiento/pausado/concluido/formalizado con transición, motivo y fecha; cierre requiere atención completa. Avances y tareas anteriores respetan pausa/cierre y alimentan el historial. Marcar un proyecto institucional como Completado exige cierre previo.
- Catálogo administrable con propuesta de doce servicios del texto proporcionado. Objetivos/resultados `[Por definir]`; niveles iniciales e hitos derivados sujetos a validación institucional. Desactivar conserva datos.
- Indicadores reales, filtros por creación/perfil/etapa y exportación CSV. Estados actuales, actividades realizadas, distribución y vencidos; sin cifras ficticias.

## Archivos

Backend: `models/incubadora.py`, `schemas/incubadora.py`, `modules/incubadora/{routes,services,registration_pdf}.py`, `main.py`, modelos exportados, integración puntual en `modules/estudiantes/mutations.py`, pruebas HTTP, calendario e inactividad, y migraciones.

Frontend: `modules/incubadora/{Incubation.jsx,incubation.css}`, `App.jsx`, `Projects.jsx`, `FullRegistration.jsx`, script `incubadora-browser.cjs` y switch `-Incubadora` del runner local. Ninguna dependencia nueva de aplicación.

Migración aditiva `f65ba0b2ad71`, posterior a `bc36a33dcdcb`: ocho tablas nuevas, FKs, unicidad, índices y CHECK; no modifica tablas existentes. Reversión solo con tablas nuevas vacías. No se ha aplicado en AWS.

## Verificación

- Suite completa de backend: 37 pruebas aprobadas en 165.581 s, sin omisiones.
- `npm test --prefix frontend`: aprobado. Se conservan los 14 destinos heredados, permisos, menús y bienvenida sin tarjetas; 56 páginas y 75 enlaces previos. Tres advertencias heredadas de StaticRouter sin fallos.
- `npm run build --prefix frontend`: aprobado; 160 módulos, JS 450.86 kB (136.67 kB gzip).
- Runner Chrome completo con `-Incubadora`: aprobado para marca/menús/login/formularios anteriores, InnovaTec y continuidad hacia diagnóstico/atención.
- Revisión adicional con `-OnlyInnovaTec -Incubadora`: aprobada incluyendo captura pública simplificada y doble envío; 320 px y escritorio.
- PDF largo renderizado y revisado: dos páginas A4, sin recortes ni página final casi vacía; marca sin alterar. Poppler solo en imagen temporal de QA.
- Verificación final focalizada: cuatro pruebas de migración, calendario/inactividad y flujo HTTP aprobadas en 88.764 s, sin omisiones.

## Cómo probar

1. Coordinador → Catálogo: configurar aviso aprobado y umbral de inactividad, cargar propuesta y completar/validar servicios e hitos.
2. `/incubadora/registro`: llenar captura, confirmar con cuenta de emprendedor y descargar PDF; abrir folio desde Proyectos.
3. Coordinador → Seguimiento → proyecto: asignar responsable, registrar actividad, responsable y revisión. Intentar omitirlos debe impedir el registro.
4. Registrar hitos y evidencia; consultar semana/vencidos e indicadores. Filtrar y exportar CSV.
5. Registrar atención de cierre y luego pausa/cierre con motivo/fecha. Recuperar una pausa mediante atención de recuperación. Verificar historial y conservación de datos.
6. Desde equipo InnovaTec acreditado, canalizar; el mismo proyecto aparece con vínculo de origen y captura de diagnóstico.

## Datos y decisiones pendientes

Aviso institucional aprobado, contactos, objetivos/resultados/canalizaciones del catálogo, validación de niveles e hitos, umbral de inactividad y eventual mecanismo de correo. No se inventan motivos estandarizados institucionales: se conserva texto obligatorio. No hay pérdida ni migración de registros anteriores a formatos ficticios. Administradores/asesores independientes corresponden a F; encuestas y difusión a D/E.
