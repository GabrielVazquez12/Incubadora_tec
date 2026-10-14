"""Serve the built portal and API from the same origin in production."""
from pathlib import Path
import mimetypes

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, Response
from sqlalchemy import text
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from app.database import engine
from app.main import app as api
from app.seo import pages, metadata, render_index, known_route, sitemap, public_origin

# Minimal Linux images may omit the system MIME database for WebP.
mimetypes.add_type("image/webp", ".webp")


class PortalFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            if exc.status_code != 404 or Path(path).suffix:
                raise
            route = '/' + path.lstrip('/')
            index = (Path(self.directory) / 'index.html').read_text(encoding='utf-8')
            return HTMLResponse(render_index(index, route, public_origin(Request(scope))), status_code=403 if route == '/403' else 200 if known_route(route) else 404,
                                headers={'Cache-Control': 'no-cache', 'X-Robots-Tag': metadata(route)['robots']})


app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware('http')
async def web_headers(request, call_next):
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    if request.url.path.startswith('/assets/') and response.status_code == 200:
        response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
    if request.url.path.startswith(('/fonts/', '/brand/')) and response.status_code == 200:
        response.headers['Cache-Control'] = 'public, max-age=86400'
    return response


@app.get('/robots.txt', response_class=PlainTextResponse)
def robots(request: Request):
    return 'User-agent: *\nAllow: /\n' + ''.join(f'Disallow: /{path}/\n' for path in ('api', 'coordinador', 'emprendedor', 'externo', 'asesor', 'innovatecnm', 'vista-previa')) + f'Sitemap: {public_origin(request).rstrip("/")}/sitemap.xml\n'


@app.get('/sitemap.xml')
def site_map(request: Request):
    return Response(sitemap(public_origin(request)), media_type='application/xml')


@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})
    return {"status": "ok"}


@app.get('/', response_class=HTMLResponse)
def public_home(request: Request):
    return HTMLResponse(render_index(Path('/app/static/index.html').read_text(encoding='utf-8'), '/', public_origin(request)), headers={'Cache-Control': 'no-cache'})


app.mount("/api", api)
app.mount("/", PortalFiles(directory="/app/static", html=True))
