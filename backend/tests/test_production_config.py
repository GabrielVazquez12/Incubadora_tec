"""Production secrets must survive URL encoding and Alembic interpolation."""
import unittest
from configparser import ConfigParser
from sqlalchemy.engine import make_url
from production_start import database_url


class ProductionConfigTest(unittest.TestCase):
    def test_password_special_characters_and_verified_tls(self):
        password = "fake@password:/%?#"
        value = database_url({"DB_USER": "app", "DB_PASSWORD": password, "DB_HOST": "db.example"})
        config = ConfigParser()
        config.add_section("alembic")
        config.set("alembic", "sqlalchemy.url", value.replace("%", "%%"))
        parsed = make_url(config.get("alembic", "sqlalchemy.url"))
        self.assertEqual(parsed.password, password)
        self.assertEqual(parsed.query["sslmode"], "verify-full")
        self.assertEqual(parsed.query["sslrootcert"], "/app/certs/rds-global-bundle.pem")

    def test_existing_database_url_is_preserved(self):
        value = "postgresql://user:password@db/local"
        self.assertEqual(database_url({"DATABASE_URL": value}), value)
