import { ImageEditor } from '../../shared/EditorialImages.jsx';
import { useEffect, useState } from 'react';
import api from '../../shared/api/client.js';
import { errorMessage } from '../../shared/portal/PortalContext.jsx';
import { Field, TextArea, Heading, Panel } from '../../shared/portal/ui.jsx';

const blank = () => ({ titulo: '', resumen: '', contenido: '', categoria: 'Noticia', fecha: new Date().toLocaleDateString('en-CA', { timeZone: 'America/Mexico_City' }), vence: '', publicada: false, destacada: false });

export default function Publications() {
  const [items, setItems] = useState([]);
  const [form, setForm] = useState(blank);
  const [id, setId] = useState(null);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  async function load() {
    try { const response = await api.get('/admin/publications'); setItems(response.data); setError(''); }
    catch (e) { setError(errorMessage(e)); }
    finally { setLoading(false); }
  }
  useEffect(() => { load(); }, []);
  const change = key => e => setForm(previous => ({ ...previous, [key]: e.target.value }));
  async function save(e) {
    e.preventDefault(); setBusy(true); setError(''); setNotice('');
    try {
      const payload = { ...form, vence: form.vence || null };
      const response = id ? await api.put(`/admin/publications/${id}`, payload) : await api.post('/admin/publications', payload);
      setId(response.data.id); setNotice('Publicación guardada. Ya puedes agregar sus imágenes y flyers.'); await load();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <><Heading eyebrow="COORDINACIÓN / COMUNICACIÓN" title="Noticias y boletín" description="Publica noticias, avisos y convocatorias en la portada. La agenda se actualiza desde el módulo Eventos." />
    {error && <p className="error" role="alert">{error} <button className="text-button" onClick={load}>Reintentar</button></p>}{notice && <p className="notice" role="status">{notice}</p>}
    <div className="two-columns"><Panel title={id ? 'Editar publicación' : 'Nueva publicación'}><form onSubmit={save}><fieldset disabled={busy} style={{ border: 0, padding: 0, minWidth: 0 }}><Field label="Título" required maxLength={160} value={form.titulo} onChange={change('titulo')} /><Field label="Categoría" value={form.categoria} onChange={change('categoria')}>{['Noticia', 'Convocatoria', 'Aviso'].map(value => <option key={value}>{value}</option>)}</Field><TextArea label="Resumen para la portada" required maxLength={500} value={form.resumen} onChange={change('resumen')} /><TextArea label="Contenido completo" required maxLength={12000} value={form.contenido} onChange={change('contenido')} /><div className="form-grid"><Field label="Fecha de publicación" type="date" required value={form.fecha} onChange={change('fecha')} /><Field label="Vigente hasta (opcional)" type="date" min={form.fecha} value={form.vence} onChange={change('vence')} /></div><p className="muted">Las fechas se interpretan en horario de Ciudad de México. Las publicaciones futuras aparecen a partir de su fecha; las vencidas dejan de aparecer.</p><label className="row"><input type="checkbox" checked={form.publicada} onChange={e => setForm({ ...form, publicada: e.target.checked })} />Publicar en el sitio</label><label className="row"><input type="checkbox" checked={form.destacada} onChange={e => setForm({ ...form, destacada: e.target.checked })} />Destacar publicación</label><div className="form-actions"><button className="button" type="submit">{busy ? 'Guardando…' : 'Guardar publicación'}</button>{id && <button type="button" className="button secondary" onClick={() => { setId(null); setForm(blank()); }}>Cancelar edición</button>}</div></fieldset></form><ImageEditor kind="publication" itemId={id} /></Panel>
    <Panel title="Publicaciones del boletín">{loading ? <p role="status">Cargando publicaciones…</p> : !items.length ? <p>Todavía no hay publicaciones.</p> : items.map(item => <article className="publication-admin-item" key={item.id}><span className="eyebrow">{item.categoria} · {item.publicada ? 'Publicada / programada' : 'Borrador'}</span><h3>{item.titulo}</h3><p className="muted">{item.resumen}</p><p className="muted">Desde {item.fecha}{item.vence ? ` · Hasta ${item.vence}` : ''}{item.destacada ? ' · Destacada' : ''}</p><button className="text-button" disabled={busy} onClick={() => { setId(item.id); setForm({ titulo: item.titulo, resumen: item.resumen, contenido: item.contenido, categoria: item.categoria, fecha: item.fecha, vence: item.vence || '', publicada: item.publicada, destacada: item.destacada }); setNotice(''); }}>Editar o retirar del sitio →</button></article>)}</Panel></div>
  </>;
}
