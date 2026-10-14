"""Prueba de integración: requiere PostgreSQL y permiso CREATE DATABASE.

Ejecutar desde backend: python -m unittest discover -s tests -v
"""
import os
import subprocess
import unittest
import uuid

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.config import settings
from app.database import Base
from app.models import Usuario, RolUsuario, Proyecto, IntegranteProyecto, Documento, HistorialEstatus


class MigracionesTest(unittest.TestCase):
    def test_esquema_nuevo_y_legacy(self):
        name = "test_incubadora_" + uuid.uuid4().hex
        admin = create_engine(settings.database_url, isolation_level="AUTOCOMMIT")
        engine = None
        created = False
        try:
            with admin.connect() as connection:
                connection.execute(text(f'CREATE DATABASE "{name}"'))
            created = True
            url = make_url(settings.database_url).set(database=name)
            engine = create_engine(url)
            env = dict(os.environ, DATABASE_URL=url.render_as_string(hide_password=False))

            def migrate(*args):
                subprocess.run(["alembic", *args], env=env, check=True, capture_output=True, text=True)

            migrate("upgrade", "head")
            configure_mappers()
            with engine.connect() as connection:
                self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
            with Session(engine) as session:
                from app.models.innovatec import ConvocatoriaInnovaTec
                call = ConvocatoriaInnovaTec(anio=2026, datos={})
                session.add(call)
                session.commit()
                with self.assertRaises(subprocess.CalledProcessError):
                    migrate('downgrade', '3a608b5c8533')
                self.assertEqual(session.scalar(text('SELECT count(*) FROM convocatorias_innovatec')), 1)
                self.assertEqual(session.scalar(text('SELECT version_num FROM alembic_version')), 'bc36a33dcdcb')
                # Only this synthetic record is removed to test the empty-table rollback below.
                session.delete(call)
                session.commit()
                user = Usuario(nombre="Prueba", correo="prueba@example.test", password_hash="test", rol=RolUsuario.estudiante)
                project = Proyecto(nombre="Prueba", propietario=user)
                session.add(project)
                session.commit()
                user_id, project_id = user.id, project.id
                with self.assertRaises(IntegrityError):
                    session.execute(text("UPDATE proyectos SET progreso = 101 WHERE id = :id"), {"id": project_id})
                session.rollback()
                session.add(Usuario(nombre="Duplicado", correo="PRUEBA@example.test", password_hash="test", rol=RolUsuario.estudiante))
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()
                session.add(IntegranteProyecto(proyecto_id=project_id, usuario_id=user_id))
                session.commit()
                session.add(IntegranteProyecto(proyecto_id=project_id, usuario_id=user_id))
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()
                session.add(IntegranteProyecto(proyecto_id=uuid.uuid4(), usuario_id=user_id))
                with self.assertRaises(IntegrityError):
                    session.commit()
                session.rollback()
                session.add_all([
                    Documento(proyecto_id=project_id, subido_por_id=user_id, nombre="Plan.pdf", tipo="plan", bucket="test", clave_archivo="plan.pdf"),
                    HistorialEstatus(proyecto_id=project_id, cambiado_por_id=user_id, estatus_nuevo="En revisión"),
                ])
                session.commit()
            migrate("downgrade", "8881ea422f6a")
            # Reproduce la instalación previa: revisión vacía y tablas con datos.
            migrate("upgrade", "head")
            with engine.connect() as connection:
                self.assertEqual(connection.scalar(text("SELECT count(*) FROM usuarios")), 1)
                self.assertEqual(connection.scalar(text("SELECT count(*) FROM proyectos")), 1)
                self.assertEqual(compare_metadata(MigrationContext.configure(connection), Base.metadata), [])
        finally:
            if engine is not None:
                engine.dispose()
            if created:
                with admin.connect() as connection:
                    connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
            admin.dispose()
