import { ImageGallery } from '../../shared/EditorialImages.jsx';
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../../shared/api/client.js';

const label = value => new Date(`${value}T12:00:00`).toLocaleDateString('es-MX', { day: 'numeric', month: 'long', year: 'numeric' });

export default function Newsletter() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);
  const [filter, setFilter] = useState('Todo');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const response = await api.get('/public/newsletter', { signal: controller.signal });
        setData(response.data); setError(false);
      } catch (e) { if (!controller.signal.aborted) setError(true); }
    }
    load();
    const timer = setInterval(load, 300000);
    window.addEventListener('focus', load);
    return () => { controller.abort(); clearInterval(timer); window.removeEventListener('focus', load); };
  }, [attempt]);
  const publications = data?.publicaciones || [];
  const events = data?.eventos || [];
  const selected = filter === 'Todo' ? publications : publications.filter(p => p.categoria === filter);
  return <section id="actualidad" className="newsletter landing-container" aria-labelledby="newsletter-title">
    <div className="newsletter-heading"><div><p className="landing-eyebrow">Boletín de la comunidad ITS</p><h1 id="newsletter-title">Lo que sucede<br /><em>en la incubadora.</em></h1></div><div><p>Noticias, convocatorias y próximas actividades. Mantente al día y encuentra tu siguiente oportunidad.</p>{data && <small>Actualizado el {new Date(data.actualizado).toLocaleDateString('es-MX', { timeZone: 'America/Mexico_City', day: 'numeric', month: 'long', year: 'numeric' })}</small>}</div></div>
    <div className="newsletter-filters" role="group" aria-label="Filtrar el boletín">{[['Todo', 'Todo'], ['Noticia', 'Noticias'], ['Convocatoria', 'Convocatorias'], ['Aviso', 'Avisos'], ['Evento', 'Eventos']].map(([value, title]) => <button key={value} type="button" aria-pressed={filter === value} onClick={() => setFilter(value)}>{title}</button>)}</div>
    {!data && !error && <p role="status">Cargando noticias y agenda…</p>}
    {error && <div className="newsletter-message" role="alert">No pudimos actualizar el boletín.{data && ' Se conserva la última información consultada.'} <button className="landing-text-link" onClick={() => setAttempt(n => n + 1)}>Reintentar</button></div>}
    {data && <div className={`newsletter-columns ${filter === 'Evento' ? 'newsletter-events-only' : ''}`}>
      {filter !== 'Evento' && <div className="newsletter-news">{selected.map((item, index) => <article key={item.id} className={`newsletter-article ${index === 0 && item.destacada ? 'newsletter-featured' : ''}`}><div className="newsletter-meta"><span>{item.categoria}</span><time dateTime={item.fecha}>{label(item.fecha)}</time></div><ImageGallery images={item.imagenes} /><h2>{item.titulo}</h2><p>{item.resumen}</p><details><summary>Leer publicación <span aria-hidden="true">↗</span></summary><div className="newsletter-body">{item.contenido.split('\n\n').map((paragraph, i) => <p key={i}>{paragraph}</p>)}</div></details>{item.vence && <small>Vigente hasta el {label(item.vence)}</small>}</article>)}{!selected.length && <p className="newsletter-message">No hay publicaciones vigentes en esta categoría.</p>}</div>}
      {(filter === 'Todo' || filter === 'Evento') && <aside className="newsletter-agenda" aria-labelledby="agenda-title"><div className="newsletter-agenda-heading"><p className="landing-eyebrow">Próximas actividades</p><h2 id="agenda-title">En la agenda</h2></div>{events.map(event => <article key={event.id} className="newsletter-event"><div className="newsletter-event-date"><strong>{event.fecha.slice(8)}</strong><span>{new Date(`${event.fecha}T12:00:00`).toLocaleDateString('es-MX', { month: 'short' })}</span></div><div><span className="newsletter-event-type">{event.tipo}</span><h3>{event.nombre}</h3><ImageGallery images={event.imagenes} /><p>{label(event.fecha)} · {event.hora.slice(0, 5)}<br />Hora de Ciudad de México · {event.modalidad}</p><p>{event.descripcion}</p><span className="newsletter-event-price">{Number(event.precio) ? `$${Number(event.precio).toLocaleString('es-MX')} MXN` : 'Gratuito'}</span><Link to="/login">Consultar inscripción →</Link></div></article>)}{!events.length && <p className="newsletter-message">Por ahora no hay actividades próximas publicadas. Consulta este espacio para conocer las nuevas fechas.</p>}<Link className="button secondary" to="/login">Acceder a mis eventos →</Link></aside>}
    </div>}
  </section>;
}
