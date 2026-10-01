"""Create the restricted application login, then migrate as that login."""
import os
import subprocess
import sys

import psycopg2
from psycopg2 import sql

from production_start import database_url


def main():
    # Only the one-off migration task receives the administrator password.
    app_user = os.environ["DB_USER"]
    if app_user == os.environ["DB_ADMIN_USER"]:
        raise ValueError("The application and administrator must be different roles")
    with psycopg2.connect(
        host=os.environ["DB_HOST"], port=int(os.environ.get("DB_PORT", "5432")),
        dbname=os.environ["DB_NAME"], user=os.environ["DB_ADMIN_USER"],
        password=os.environ["DB_ADMIN_PASSWORD"], sslmode="verify-full",
        sslrootcert=os.environ.get("DB_SSLROOTCERT", "/app/certs/rds-global-bundle.pem"),
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (app_user,))
            if cursor.fetchone() is None:
                cursor.execute(sql.SQL("CREATE ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(app_user)),
                               (os.environ["DB_PASSWORD"],))
            else:
                cursor.execute(sql.SQL("ALTER ROLE {} LOGIN PASSWORD %s").format(sql.Identifier(app_user)),
                               (os.environ["DB_PASSWORD"],))
            cursor.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(os.environ["DB_NAME"]), sql.Identifier(app_user)))
            cursor.execute(sql.SQL("GRANT USAGE, CREATE ON SCHEMA public TO {}").format(sql.Identifier(app_user)))
    os.environ["DATABASE_URL"] = database_url(os.environ)
    os.environ.pop("DB_ADMIN_PASSWORD", None)
    return subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"])


if __name__ == "__main__":
    sys.exit(main())
