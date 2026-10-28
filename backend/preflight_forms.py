"""Read-only form integrity audit before applying the production migration."""
import importlib.util
import json
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from production_start import database_url
from app.initial_registration import validate_data, merge_files


def main():
    migration = Path(__file__).parent / "alembic/versions/3a608b5c8533_form_integrity.py"
    spec = importlib.util.spec_from_file_location("form_migration", migration)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    queries = {
        "usuarios.correo_duplicado": "SELECT count(*) FROM (SELECT lower(btrim(correo)) FROM usuarios GROUP BY lower(btrim(correo)) HAVING count(*) > 1) d",
        "tipos_evento.nombre_duplicado": "SELECT count(*) FROM (SELECT lower(btrim(nombre)) FROM tipos_evento GROUP BY lower(btrim(nombre)) HAVING count(*) > 1) d",
        "tutorias.reserva_duplicada": "SELECT count(*) FROM (SELECT slot FROM tutorias WHERE estatus = 'Confirmada' GROUP BY slot HAVING count(*) > 1) d",
    }
    queries.update({f"{table}.{name}": f'SELECT count(*) FROM "{table}" WHERE NOT ({condition})'
                    for table, checks in module.CHECKS.items() for name, condition in checks.items()})
    engine = create_engine(database_url(os.environ))
    try:
        with engine.connect() as connection:
            version = connection.scalar(text("SELECT version_num FROM alembic_version"))
            counts = {key: connection.scalar(text(query)) for key, query in queries.items()}
            counts["registros_iniciales.datos_incompatibles"] = 0
            counts["registros_iniciales.administracion_incompatible"] = 0
            for row in connection.execute(text("SELECT datos, administracion, archivos, estatus FROM registros_iniciales")):
                if row.estatus in ("Pendiente", "En revisión", "Aprobado"):
                    try:
                        validate_data(row.datos, complete=True)
                        merge_files(row.datos, row.archivos, {}, complete=True)
                    except Exception:
                        counts["registros_iniciales.datos_incompatibles"] += 1
                try:
                    validate_data(row.administracion or {}, administrative=True, participant_data=row.datos)
                except Exception:
                    counts["registros_iniciales.administracion_incompatible"] += 1
        print(json.dumps({"migration": version, "violations": counts}, ensure_ascii=False), flush=True)
        if any(counts.values()):
            raise RuntimeError("La base contiene registros incompatibles. Revisarlos sin alterarlos automáticamente.")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
