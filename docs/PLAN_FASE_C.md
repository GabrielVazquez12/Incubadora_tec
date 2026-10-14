# Fase C: expediente y seguimiento de la Incubadora

Se conserva `Proyecto` como identidad única, además de Solicitudes, Registros, Avances, Tareas y Documentos. No se sustituye la aprobación del formato previo ni se modifican contratos anteriores. El diagnóstico nuevo será un complemento enlazado al proyecto o registro de ingreso; su aprobación continuará por el flujo actual. La canalización InnovaTec utiliza el Proyecto ya creado.

1. Añadir catálogo, hitos, diagnóstico enlazado, atenciones, canalizaciones y configuración mediante migración aditiva reversible solo con tablas nuevas vacías. Responsables usan usuarios reales y permisos existentes; el rol de asesor independiente se añade en F.
2. API: catálogo público/administrable; diagnóstico, estado y frecuencia versionados; bitácora con actividad/responsable/revisión obligatorios; hitos y evidencias; vistas semana/vencidos/inactivos; reactivación trazable; indicadores de datos reales y CSV. Validaciones de permisos, propiedad, fechas, tipos y transiciones en servidor.
3. UI: integrar expediente desde Proyectos/Seguimiento y Mis avances; sustituir marcadores de catálogo, hitos, seguimientos e indicadores. Registro público enlaza el registro existente con diagnóstico adicional y privacidad configurable. PDF con la imagen oficial sin inventar firmas.
4. Pruebas críticas y regresión completa antes de D: cierre incompleto, transiciones, próxima revisión, inactividad, permisos, relaciones, indicadores y PDF.

Catálogo inicial usa los doce servicios proporcionados; objetivos/resultados no entregados muestran `[Por definir]`. Los hitos iniciales son propuestas explícitas sujetas a validación. No se inventa umbral de inactividad ni motivos institucionales: administrador configura los primeros; texto obligatorio conserva el motivo. Recordatorios únicamente en pantalla, porque no hay mecanismo de correo verificado. Los contactos no se inventan.
