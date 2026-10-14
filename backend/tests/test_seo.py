import unittest
from xml.etree import ElementTree as ET
from app.seo import metadata, render_index, sitemap, pages, known_route


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
