# Fase D: encuestas

La búsqueda en modelos, rutas y módulos confirmó que solo existe el marcador visual de encuestas. Se añade un módulo siguiendo FastAPI/SQLAlchemy, DTOs estrictos y componentes existentes; sin dependencias nuevas.

1. Migración aditiva: encuesta, preguntas y respuestas. Unicidad encuesta/identidad; anonimato no conserva correo/nombre/IP. Ediciones versionadas y diseño congelado tras recibir respuestas para no corromper resultados. Rollback conserva datos.
2. Constructor de título/descripción/público, cuatro tipos de pregunta, obligatoriedad, fechas, anonimato/publicación. Plantillas iniciales editables como borradores, sin precargar respuestas ficticias.
3. Respuesta pública: valores exactos, rangos y texto acotado; identificada usa usuario real del token. Anónima usa cookie firmada HttpOnly y unicidad en BD. No equivale a verificar una persona única si borra cookies o cambia navegador; documentar ese límite.
4. Resultados solo coordinación: conteos/porcentajes, barras/dona accesibles y CSV. Referencias proporcionadas se identifican como diagnóstico histórico; nunca se suman a respuestas reales.
5. Rutas `/encuestas`, `/encuestas/:id`, `/admin/encuestas` y submenús actuales; enlaces desde Boletín, sin accesos en la bienvenida. Pruebas de permisos, datos inválidos, duplicados, fechas, edición y estadísticas; build/regresión antes de E.
