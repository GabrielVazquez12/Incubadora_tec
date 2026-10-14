# Fase B: InnovaTec

Se extiende `Innovacion`, sin sustituir sus rutas, categorías, revisión ni JSON histórico. Los datos del proyecto permanecen allí; el expediente de equipo lo referencia mediante FK única. Pláticas usan `Evento` e `Inscripcion`; no se crean inscripciones paralelas. Se reutilizan almacenamiento privado, validación de documentos, JWT, componentes y CSV existentes. Sin dependencias nuevas.

1. Modelos `models/innovatec.py`, DTOs `schemas/innovatec.py` y migración aditiva: convocatoria, expediente, integrantes, documentos y pláticas. Estados, llaves, unicidad y rangos protegidos en servidor y BD. Reversión solo con tablas nuevas vacías; rollback de aplicación puede conservar esquema/datos.
2. `modules/innovacion/`: endpoints públicos de consulta y autenticados de captura/gestión, transiciones con bloqueo y versión, revisión/documentos privados, seguimiento, diplomas y canalización idempotente a Proyecto. Registro de quién/qué/cuándo en el historial. Sin cambiar endpoints actuales.
3. React: convocatoria, inscripción/equipos/expediente, pláticas y diplomas en las rutas previstas; sustituir únicamente sus marcadores de Fase A e integrar acceso desde propuesta e inscripciones existentes. Mismos menús y permisos. El público consulta; la cuenta existente confirma. Captura anónima requiere respuesta del usuario.
4. Pruebas de tipos, integridad, permisos/IDOR, documentos, estados, canalización y concurrencia; migración nueva/legacy/reversión, suite existente, Chrome y build. No pasar a C con fallos. Commit por funcionalidad y documentación de resultados.

Datos no proporcionados no se siembran: convocatoria/manual, fechas/sedes, requisitos, aviso aprobado y contactos. Gestión admite borradores. Publicar exige fechas coherentes y aviso aprobado; consentimiento conserva texto/versión/fecha. No se simulan correos. Los diplomas digitales usan ReportLab existente y la imagen oficial completa, sin inventar firmas ni sellos; pláticas conservan las constancias existentes.

Fases posteriores: C (expediente/bitácora/catálogo), D (encuestas), E (difusión/eventos/vinculación), F (roles/auditoría/SEO/accesibilidad/documentación). Cada fase se verifica antes de continuar. Despliegue con migración requiere primero backup y preflight sobre la revisión anterior; nunca downgrade destructivo en producción.
