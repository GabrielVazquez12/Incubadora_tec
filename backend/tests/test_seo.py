import unittest
from xml.etree import ElementTree as ET
from app.seo import metadata, render_index, sitemap, pages, known_route, public_origin
from unittest.mock import patch
from types import SimpleNamespace
from starlette.datastructures import URL


class SeoTest(unittest.TestCase):
    def test_public_manifest_and_private_noindex(self):
        self.assertEqual(metadata('/incubadora')['robots'], 'index, follow')
        for route in ['/coordinador/usuarios', '/login', '/registro', '/encuestas/private', '/not-found']:
            self.assertEqual(metadata(route)['robots'], 'noindex, nofollow')
        self.assertTrue(known_route('/coordinador'))
        for route in ['/incubadora/proyectos', '/incubadora/proyectos/existing', '/incubadora/indicadores', '/innovatec/equipos', '/innovatec/seguimiento']:
            self.assertTrue(known_route(route), route)
            self.assertEqual(metadata(route)['robots'], 'noindex, nofollow')
        self.assertFalse(known_route('/does-not-exist'))
        self.assertNotIn('/incubadora/registro', pages())

    def test_server_metadata_and_safe_discovery(self):
        markup = '<head><title>Old</title><meta name="description" content="Old" /><meta property="og:title" content="Old" /></head>'
        result = render_index(markup, '/incubadora', 'https://example.com')
        self.assertIn('Incubadora de Empresas · Enlaces', result)
        self.assertIn('index, follow', result)
        self.assertIn('href="https://example.com/incubadora"', result)
        self.assertNotIn('content="Old"', result)
        self.assertIn('as="image"', render_index(markup, '/'))
        self.assertNotIn('as="image"', render_index(markup, '/login'))
        tree = ET.fromstring(sitemap('https://example.com/'))
        urls = [child[0].text for child in tree]
        self.assertEqual(len(urls), len(pages()))
        self.assertTrue(all(url.startswith('https://example.com/') for url in urls))
        self.assertFalse(any('/coordinador' in url for url in urls))

    def test_proxy_scheme_is_limited_to_configured_peers_and_metadata(self):
        request = SimpleNamespace(base_url=URL('http://portal.example/'), client=SimpleNamespace(host='10.42.10.20'), headers={'x-forwarded-proto': 'https'})
        with patch.dict('os.environ', {'SEO_TRUSTED_PROXY_CIDRS': '10.42.10.0/24,10.42.11.0/24'}):
            self.assertEqual(public_origin(request), 'https://portal.example/')
            self.assertEqual(str(request.base_url), 'http://portal.example/')
            request.headers['x-forwarded-proto'] = 'https, http'
            self.assertEqual(public_origin(request), 'http://portal.example/')
            request.headers['x-forwarded-proto'] = 'https'
            request.client.host = '198.51.100.12'
            self.assertEqual(public_origin(request), 'http://portal.example/')
            request.client.host = 'testclient'
            self.assertEqual(public_origin(request), 'http://portal.example/')
            request.client.host = '10.42.10.20'
        with patch.dict('os.environ', {'SEO_TRUSTED_PROXY_CIDRS': ''}):
            self.assertEqual(public_origin(request), 'http://portal.example/')
