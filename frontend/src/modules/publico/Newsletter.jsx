import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { ImageGallery } from '../../shared/EditorialImages.jsx';
import { Modal } from '../../shared/portal/ui.jsx';
import api from '../../shared/api/client.js';
import './newsletter.css';

const label = value => new Date(`${value}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });
const searchable = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es-MX');

export function PublicationCard({ item, featured = false, onRead }) {
  return <article className={`news-card ${featured ? 'news-card-featured' : ''}`}>
    {item.imagenes?.length > 0 && <div className="news-cover"><ImageGallery images={item.imagenes.slice(0, 1)} variant="cover" /></div>}
    <div className="news-card-content"><div className="news-meta"><span>{item.categoria}</span>{featured && <span className="news-featured-label">Destacada</span>}<time dateTime={item.fecha}>{label(item.fecha)}</time></div>
      <h2><button type="button" onClick={() => onRead(item)}>{item.titulo}</button></h2><p>{item.resumen}</p>
      <div className="news-card-footer"><button className="news-read" type="button" onClick={() => onRead(item)}>Leer noticia <span aria-hidden="true">→</span></button>{item.imagenes?.length > 1 && <span>{item.imagenes.length} imágenes</span>}</div>
      {item.vence && <small>Vigente hasta el {label(item.vence)}</small>}
    </div>
  </article>;
}

export default function Newsletter({ portalBase = '', compact = false }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState('Todo');
  const [search, setSearch] = useState('');
  const [attempt, setAttempt] = useState(0);
  const [params, setParams] = useSearchParams();
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await api.get('/public/newsletter', { signal: controller.signal });
        if (!controller.signal.aborted) { setData(response.data); setError(false); }
      } catch (e) { if (!controller.signal.aborted) setError(true); }
    }
    load();
    const timer = setInterval(load, 300000);
    window.addEventListener('focus', load);
    return () => { controller.abort(); clearInterval(timer); window.removeEventListener('focus', load); };
  }, [attempt]);
  const publications = data?.publicaciones || [];
  const query = searchable(search.trim());
  const matches = value => searchable(value).includes(query);
  const selected = publications.filter(item => (filter === 'Todo' || item.categoria === filter) && matches(`${item.titulo} ${item.resumen} ${item.contenido}`));
  const events = (data?.eventos || []).filter(event => matches(`${event.nombre} ${event.descripcion} ${event.tipo}`));
  const visible = compact ? selected.slice(0, 3) : selected;
  const article = publications.find(item => item.id === params.get('noticia'));
  const openArticle = item => { const next = new URLSearchParams(params); next.set('noticia', item.id); setParams(next, { preventScrollReset: true }); };
  const closeArticle = () => { const next = new URLSearchParams(params); next.delete('noticia'); setParams(next, { replace: true, preventScrollReset: true }); };
  const eventPath = portalBase ? `${portalBase}/eventos` : '/login';
  const showEvents = !compact && (filter === 'Todo' || filter === 'Evento');
  return <section id="actualidad" className={`newsletter ${portalBase ? 'newsletter-portal' : 'landing-container'} ${compact ? 'newsletter-compact' : ''}`} aria-labelledby="newsletter-title">
    <header className="news-heading"><div><p className="news-eyebrow">Boletín de la comunidad ITS</p>{compact ? <h2 id="newsletter-title">Entérate de lo que sucede</h2> : <h1 id="newsletter-title">Actualidad de la incubadora</h1>}<p>Noticias, convocatorias y actividades para nuestra comunidad.</p></div><div className="news-heading-actions">{compact ? <Link className="news-read" to={`${portalBase}/boletin`}>Ver todo el boletín →</Link> : <>{data && <small>Actualizado el {new Date(data.actualizado).toLocaleDateString('es-MX', { timeZone: 'America/Mexico_City', day: 'numeric', month: 'long', year: 'numeric' })}</small>}<button type="button" className="news-read" onClick={() => setAttempt(n => n + 1)}>Actualizar noticias ↻</button></>}</div></header>
    {!compact && <div className="news-tools"><div className="news-filters" role="group" aria-label="Filtrar el boletín">{[['Todo', 'Todo'], ['Noticia', 'Noticias'], ['Convocatoria', 'Convocatorias'], ['Aviso', 'Avisos'], ['Evento', 'Eventos']].map(([value, title]) => <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)}>{title}</button>)}</div><label className="news-search"><span>Buscar en el boletín</span><input type="search" value={search} onChange={e => setSearch(e.target.value)} placeholder="Noticia, taller, convocatoria…" /></label></div>}
    {!data && !error && <p className="news-message" role="status">Cargando noticias y agenda…</p>}
    {error && <div className="news-message" role="alert">No pudimos actualizar el boletín.{data && ' Se conserva la última información consultada.'} <button className="news-read" type="button" onClick={() => setAttempt(n => n + 1)}>Reintentar</button></div>}
    {data && <>
      {!compact && <p className="news-result-count" role="status">{filter === 'Evento' ? 0 : selected.length} publicaciones{showEvents ? ` · ${events.length} próximos eventos` : ''}{query ? ` para “${search.trim()}”` : ''}</p>}
      <div className={`news-columns ${showEvents ? 'news-with-agenda' : ''} ${filter === 'Evento' ? 'news-events-only' : ''}`}>
        {filter !== 'Evento' && <div className="news-grid">{visible.map((item, index) => <PublicationCard key={item.id} item={item} featured={!compact && index === 0 && item.destacada} onRead={openArticle} />)}{!visible.length && <p className="news-message">{query ? 'No encontramos noticias con esa búsqueda. Prueba con otro término.' : 'No hay publicaciones vigentes en esta categoría.'}</p>}</div>}
        {showEvents && <aside className="news-agenda" aria-labelledby="agenda-title"><div className="news-agenda-heading"><p className="news-eyebrow">Próximas actividades</p><h2 id="agenda-title">En la agenda</h2></div><div className="news-events">{events.map(event => <article key={event.id} className="news-event">{event.imagenes?.length > 0 && <ImageGallery images={event.imagenes.slice(0, 1)} variant="cover" />}<div className="news-event-content"><div className="news-event-heading"><div className="news-date"><strong>{event.fecha.slice(8)}</strong><span>{new Date(`${event.fecha}T12:00:00`).toLocaleDateString('es-MX', { month: 'short' })}</span></div><div><span className="news-event-type">{event.tipo}</span><h3>{event.nombre}</h3></div></div><p>{label(event.fecha)} · {event.hora.slice(0, 5)}<br />Hora de Ciudad de México · {event.modalidad}</p><p>{event.descripcion}</p><div className="news-card-footer"><span className="news-event-price">{Number(event.precio) ? `$${Number(event.precio).toLocaleString('es-MX')} MXN` : 'Gratuito'}</span><Link className="news-read" to={eventPath}>Ver evento →</Link></div></div></article>)}</div>{!events.length && <p className="news-message">{query ? 'No encontramos eventos con esa búsqueda.' : 'Pronto compartiremos nuevas actividades aquí.'}</p>}<Link className="news-read news-agenda-link" to={eventPath}>Consultar eventos e inscripciones →</Link></aside>}
      </div>
    </>}
    {article && <Modal title={article.titulo} onClose={closeArticle}><div className="news-reader"><div className="news-meta"><span>{article.categoria}</span><time dateTime={article.fecha}>{label(article.fecha)}</time></div><ImageGallery images={article.imagenes} variant="cover" /><p className="news-reader-summary">{article.resumen}</p><div className="news-body">{article.contenido.split('\n\n').map((paragraph, index) => <p key={index}>{paragraph}</p>)}</div>{article.vence && <small>Vigente hasta el {label(article.vence)}</small>}<Link className="news-read" to={`/?noticia=${article.id}#actualidad`}>Enlace público de esta noticia ↗</Link></div></Modal>}
  </section>;
}