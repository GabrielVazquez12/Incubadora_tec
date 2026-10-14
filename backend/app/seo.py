"""Shared public route manifest; never include authenticated records in discovery."""
from functools import lru_cache
import json
import os
from ipaddress import ip_address, ip_network
import re
from html import escape
from pathlib import Path


def public_origin(request):
    """Use the load balancer scheme only for metadata, from configured networks."""
    origin = request.base_url
    forwarded = request.headers.get('x-forwarded-proto')
    if request.client and forwarded in ('http', 'https'):
        try:
            peer = ip_address(request.client.host)
        except ValueError:
            return str(origin)
        networks = (ip_network(value.strip()) for value in os.environ.get('SEO_TRUSTED_PROXY_CIDRS', '').split(',') if value.strip())
        if any(peer in network for network in networks):
            origin = origin.replace(scheme=forwarded)
    return str(origin)


@lru_cache(maxsize=1)
def pages():
    static = Path('/app/static/site-pages.json')
    source = static if static.exists() else Path(__file__).resolve().parents[2] / 'frontend/public/site-pages.json'
    return json.loads(source.read_text(encoding='utf-8'))


def metadata(path):
    page = pages().get(path)
    return {'title': f'{page[0]} · Enlaces Institucionales ITS' if page else 'Enlaces Institucionales ITS',
            'description': page[1] if page else 'Portal de Enlaces Institucionales del Instituto Tecnológico de Saltillo.',
            'robots': 'index, follow' if page else 'noindex, nofollow'}


def render_index(index, path, origin=""):
    meta = metadata(path)
    result = re.sub(r'<title>.*?</title>', f'<title>{escape(meta["title"])}</title>', index, flags=re.S)
    for key, value in [('description', meta['description']), ('og:title', meta['title']), ('og:description', meta['description'])]:
        result = re.sub(r'<meta (name|property)="' + re.escape(key) + r'" content="[^"]*"\s*/?>', lambda match: f'<meta {match[1]}="{key}" content="{escape(value, quote=True)}" />', result)
    discovery = f'<meta name="robots" content="{meta["robots"]}" />'
    if origin and path in pages():
        url = escape(origin.rstrip('/') + path, quote=True)
        discovery += f'<link rel="canonical" href="{url}" /><meta property="og:url" content="{url}" />'
        result = result.replace('content="/brand/enlaces-institucionales.jpeg"', f'content="{escape(origin.rstrip("/"), quote=True)}/brand/enlaces-institucionales.jpeg"')
    if path == '/':
        discovery += '<link rel="preload" as="image" type="image/webp" href="/brand/enlaces-institucionales-400.webp" imagesrcset="/brand/enlaces-institucionales-400.webp 400w, /brand/enlaces-institucionales-800.webp 800w, /brand/enlaces-institucionales-1200.webp 1200w" imagesizes="(min-width: 768px) 25vw, 46vw" fetchpriority="high" />'
    return result.replace('</head>', discovery + '</head>')


def known_route(path):
    aliases = ('/incubadora/proyectos', '/incubadora/seguimientos', '/incubadora/inactivos', '/incubadora/indicadores', '/innovatec/equipos', '/innovatec/diplomas', '/innovatec/seguimiento')
    return any(path == route or path.startswith(route + '/') for route in aliases) or path in pages() or path in ('/coordinador', '/emprendedor', '/externo', '/innovatecnm', '/vista-previa', '/login', '/registro', '/403', '/incubadora/registro', '/innovatec/inscripcion') or any(path.startswith(prefix) for prefix in ('/coordinador/', '/emprendedor/', '/externo/', '/innovatecnm/', '/vista-previa/', '/asesor/')) or bool(re.fullmatch(r'/(eventos|encuestas)/[0-9a-fA-F-]{36}', path)) or path.startswith('/incubadora/catalogo/')


def sitemap(origin):
    urls = ''.join(f'<url><loc>{escape(origin.rstrip("/") + path)}</loc></url>' for path in pages())
    return f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
