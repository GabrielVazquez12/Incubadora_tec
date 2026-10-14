import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import pages from '../../../public/site-pages.json';

export default function Seo() {
  const { pathname } = useLocation();
  useEffect(() => {
    const page = pages[pathname];
    const title = page ? `${page[0]} · Enlaces Institucionales ITS` : 'Enlaces Institucionales ITS';
    const description = page?.[1] || 'Portal de Enlaces Institucionales del Instituto Tecnológico de Saltillo.';
    document.title = title;
    let canonical = document.head.querySelector('link[rel="canonical"]');
    if (page) {
      if (!canonical) { canonical = document.createElement('link'); canonical.rel = 'canonical'; document.head.append(canonical); }
      canonical.href = window.location.origin + pathname;
    } else canonical?.remove();
    for (const [attribute, name, content] of [['name', 'description', description], ['name', 'robots', page ? 'index, follow' : 'noindex, nofollow'], ['property', 'og:title', title], ['property', 'og:description', description]]) {
      let tag = document.head.querySelector(`meta[${attribute}="${name}"]`);
      if (!tag) { tag = document.createElement('meta'); tag.setAttribute(attribute, name); document.head.append(tag); }
      tag.content = content;
    }
  }, [pathname]);
  return null;
}
