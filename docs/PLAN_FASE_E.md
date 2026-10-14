# Fase E: difusión, eventos y vinculación

La revisión confirmó `Publication`, galería `EditorialImage`, `Evento`, `Inscripcion` y asistencia/constancias, pero no calendario de difusión, visitas, plantillas, FAQ ni bandeja de contacto. Se extienden esas entidades; no se duplican noticias o inscripciones.

1. Migración aditiva para piezas, visitas, plantillas y registro manual de envíos, FAQ, configuración institucional, contacto y fichas de eventos (FK opcional a Evento). Versiones/historial, relaciones, estados y límites de entrada. Rollback solo con tablas nuevas vacías.
2. APIs privadas para coordinación y públicas de consulta/contacto. Responsables son cuentas reales; enlaces HTTP/HTTPS sin credenciales, datos personales protegidos y consentimiento aprobado. Registro manual de difusión/envíos; no se envían mensajes a personas ni se simula correo.
3. Difusión integra noticias/galería existentes y cinco ejes. Publicación multicanal, visitas a salones, plantillas para alumnos/docentes, orientación/FAQ y contenidos enlazados. Nuevas capacidades solo en submenús, sin alterar bienvenida ni módulos de pagos.
4. Eventos públicos listados/detalle con imágenes/fecha/lugar y acceso a inscripción existente. Las tres fichas iniciales usan únicamente títulos/lema proporcionados y muestran fechas/lugares por definir; no se crean eventos operativos con fechas inventadas. Coordinación puede enlazarlas a eventos reales.
5. Vinculación y contacto con contenido configurable/marcadores; inbox privado y confirmación de recepción. Los contactos/redes permanecen vacíos hasta configurarse con datos reales. Tests de permisos, validaciones, reintentos, archivos/galerías y compatibilidad; build y Chrome antes de F.
