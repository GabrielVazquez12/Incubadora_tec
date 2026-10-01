"""Serve the built portal and API from the same origin in production."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

from app.database import engine
from app.main import app as api


class PortalFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or Path(path).suffix:
                raise
            return FileResponse(Path(self.directory) / "index.html", headers={"Cache-Control": "no-cache"})


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}


app.mount("/api", api)
app.mount("/", PortalFiles(directory="/app/static", html=True))
