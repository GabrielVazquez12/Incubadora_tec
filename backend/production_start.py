"""Production entry point; construct the DB URL without logging credentials."""
import os
import subprocess
import sys

from sqlalchemy.engine import URL


def database_url(environ):
    if environ.get("DATABASE_URL"):
        return environ["DATABASE_URL"]
    query = {"sslmode": environ.get("DB_SSLMODE", "verify-full")}
    if query["sslmode"] in ("verify-full", "verify-ca"):
        query["sslrootcert"] = environ.get("DB_SSLROOTCERT", "/app/certs/rds-global-bundle.pem")
    return URL.create(
        "postgresql+psycopg2", username=environ["DB_USER"],
        password=environ["DB_PASSWORD"], host=environ["DB_HOST"],
        port=int(environ.get("DB_PORT", "5432")),
        database=environ.get("DB_NAME", "incubadora"), query=query,
    ).render_as_string(hide_password=False)


def main():
    os.environ["DATABASE_URL"] = database_url(os.environ)
    # Migrations run as a separate, one-off task before publishing a revision.
    if sys.argv[1:] == ["migrate"]:
        return subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"])
    os.execvp(sys.executable, [sys.executable, "-m", "uvicorn", "app.production:app",
                             "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    sys.exit(main())
