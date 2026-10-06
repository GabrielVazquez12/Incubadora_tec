import { useState } from 'react';
import { Link } from 'react-router-dom';
import { usePortal } from '../../shared/portal/PortalContext.jsx';
import { usePortalRoute } from '../../shared/portal/PortalLayout.jsx';
import { today, uid, dateLabel } from '../../shared/portal/data.js';
import { Badge, Field, Heading, Modal, Panel, Stats, Table, TextArea, exportCSV, formValues } from '../../shared/portal/ui.jsx';

const catalogs = {
  certamen: { title: 'Certamen de Proyectos', description: 'Selecciona el área que mejor representa tu propuesta de innovación.', items: [
    ['Sector Agroindustrial', 'Campo, pesca, acuacultura, tecnificación y sostenibilidad.'],
    ['Industria Eléctrica y Electrónica', 'Hardware, potencia, control, semiconductores y sistemas embebidos.'],
    ['Sector Energético y Electromovilidad', 'Energías renovables, almacenamiento, vehículos e infraestructura de recarga.'],
    ['Tecnologías para la Salud Humana', 'Salud digital, telemedicina, dispositivos médicos y biotecnología.'],
    ['Sostenibilidad Ambiental', 'Restauración ambiental, resiliencia y comunidades sostenibles.'],
    ['Bienes de Consumo Final', 'Productos y servicios para el consumidor final.'],
  ] },
  hackatec: { title: 'HackaTec', description: 'Un reto, un equipo y nuevas maneras de resolver problemas.', items: ['Ecosistemas de Desarrollo', 'Tecnologías Emergentes', 'Tecnologías para la Gestión Pública', 'Tecnologías para el Entretenimiento', 'Software Inteligente', 'HackaHer'].map(t => [t, 'Registra a tu equipo y organiza su propuesta de solución.']) },
  innobotica: { title: 'InnoBótica', description: 'Ingeniería, creatividad y tecnología en movimiento.', items: ['Robots Minisumo', 'Robots Seguidores de Línea', 'Robótica Aplicada', 'Robots Humanoides', 'Robots Buscadores', 'Vehículos Aéreos No Tripulados (VANT)', 'Sistemas Aeroespaciales tipo CanSat', 'Robot Soccer', 'Exhibición de Robótica Bioinspirada'].map(t => [t, 'Consulta tu categoría y prepara la participación de tu equipo.']) },
  innovaccion: { title: 'InnovAcción', description: 'Conecta tus ideas con nuevas oportunidades de transformación.', items: [['InnovAcción', 'Prepara una propuesta de participación. La convocatoria institucional definirá sus requisitos y fechas.']] },
  retos: { title: 'Retos de Transformación Nacional', description: 'Propuestas tecnológicas para los desafíos de nuestro entorno.', items: [['Retos de Transformación Nacional', 'Registra una propuesta. La institución definirá los retos y las condiciones de participación.']] },
};

export default function Innovation({ section = 'inicio' }) {
  const { data, update, notify, busy } = usePortal();
  const { base, query, role, userId } = usePortalRoute();
  const [category, setCategory] = useState(null);
  const [detail, setDetail] = useState(null);
  const [error, setError] = useState('');
  const [editing, setEditing] = useState(false);
  const [status, setStatus] = useState('');
  const [search, setSearch] = useState('');
  const catalog = catalogs[section];
  const records = data.innovation.filter(r => role === 'admin' || r.user === userId);
  const shown = records.filter(r => (!status || r.estatus === status) && `${r.nombre} ${r.equipo} ${r.modulo}`.toLowerCase().includes(search.toLowerCase()));
  const current = detail && records.find(r => r.id === detail.id);
  const editable = current && role !== 'admin' && ['Borrador', 'Correcciones solicitadas'].includes(current.estatus);
  function closeDetail() { setDetail(null); setEditing(false); setError(''); }
  async function saveProposal(e) {
    e.preventDefault();
    const nextStatus = e.nativeEvent.submitter?.value || 'Borrador';
    const changes = { ...current, ...formValues(e), estatus: nextStatus, estatus_anterior: current.estatus };
    if (await update('innovation', changes)) { closeDetail(); notify(nextStatus === 'En revisión' ? 'Propuesta enviada a coordinación.' : 'Propuesta guardada.'); }
  }
  async function review(e) {
    e.preventDefault();
    if (await update('innovation', { ...current, ...formValues(e), estatus_anterior: current.estatus })) { closeDetail(); notify('Seguimiento actualizado.'); }
  }
  const sourceNote = <p className="helper">Registro interno de propuestas. La participación oficial está sujeta a las convocatorias institucionales.</p>;
  async function register(e) {
    e.preventDefault(); const values = formValues(e);
    if (records.some(r => r.nombre.toLowerCase() === values.nombre.trim().toLowerCase() && r.modulo === catalog.title && r.categoria === category)) { setError('Ya existe una propuesta con ese nombre en esta categoría.'); return; }
    if (!await update('innovation', { ...values, nombre: values.nombre.trim(), id: uid(), user: userId, modulo: catalog.title, categoria: category, etapa: 'Local', estatus: 'Borrador', fecha: today() })) return; setCategory(null); setError(''); notify('Propuesta guardada. Puedes verla en Registros.');
  }
  return <><Heading eyebrow="INNOVATECNM / INNOVACIÓN Y EMPRENDIMIENTO" title={section === 'inicio' ? 'InnovaTecNM' : section === 'registros' ? 'Registro y seguimiento' : catalog.title} description={catalog?.description || 'Cumbre Nacional de Desarrollo Tecnológico, Emprendimiento e Innovación'} action={section !== 'registros' && <Link className="button secondary" to={`${base}/registros${query}`}>Ver registros</Link>} />
    {section === 'inicio' ? <><div className="innovation-hero"><p className="eyebrow">EL TALENTO TRANSFORMA</p><h2>Grandes ideas.<br />Impacto real.</h2><p>Un espacio para desarrollar proyectos, resolver retos y construir el futuro en equipo.</p><div className="stage-row"><span>01 · Local</span><span>02 · Regional</span><span>03 · Nacional</span></div></div><Stats items={[[ 'Certamen de Proyectos', '6', 'Categorías de participación'], ['HackaTec', '6', 'Retos para tu equipo'], ['InnoBótica', '8 + 1', 'Categorías y exhibición'], ['Otros eventos', '2', 'InnovAcción y Retos Nacionales']]} /><div className="module-grid">{Object.entries(catalogs).map(([key, value], index) => <Link className="module-card" key={key} to={`${base}/${key}${query}`}><span className="module-number">0{index + 1}</span><h2>{value.title}</h2><p>{value.description}</p><span className="module-arrow">↗</span></Link>)}</div>{sourceNote}</> : section === 'registros' ? <Panel title={role === 'admin' ? 'Propuestas registradas' : 'Mis propuestas'}><div className="filters"><Field label="Buscar propuesta o equipo" value={search} onChange={e => setSearch(e.target.value)} /><Field label="Estado de la propuesta" value={status} onChange={e => setStatus(e.target.value)}><option value="">Todos los estados</option>{['Borrador', 'En revisión', 'Correcciones solicitadas', 'Aprobada', 'Rechazada'].map(t => <option key={t}>{t}</option>)}</Field><button className="button secondary" onClick={() => exportCSV('propuestas-innovacion.csv', ['Proyecto', 'Equipo', 'Evento', 'Categoría', 'Etapa', 'Estado', 'Observaciones'], shown.map(r => [r.nombre, r.equipo, r.modulo, r.categoria, r.etapa, r.estatus, r.observaciones]))}>Exportar CSV</button></div><Table headings={['Proyecto / equipo', 'Evento', 'Categoría', 'Etapa', 'Estado', 'Acción']} empty={!shown.length}>{shown.map(r => <tr key={r.id}><td><strong>{r.nombre}</strong><small>{r.equipo}</small></td><td>{r.modulo}</td><td>{r.categoria}</td><td>{r.etapa}</td><td><Badge>{r.estatus}</Badge></td><td><button className="text-button" onClick={() => { setDetail(r); setEditing(false); setError(''); }}>Ver detalle</button></td></tr>)}</Table></Panel> : <><div className="category-grid">{catalog.items.map(([title, description], index) => <article className="category-card" key={title}><span className="category-number">{String(index + 1).padStart(2, '0')}</span><div><h2>{title}</h2><p className="muted">{description}</p>{role === 'admin' ? <Link className="text-link" to={`${base}/registros${query}`}>Consultar propuestas →</Link> : <button className="text-button" onClick={() => { setCategory(title); setError(''); }}>Preparar registro →</button>}</div></article>)}</div>{sourceNote}</>}
    {category && role !== 'admin' && <Modal title="Preparar registro" onClose={() => setCategory(null)}><p className="info-box">{catalog.title} · {category}</p><form className="form-stack" data-unsaved="true" onSubmit={register}><Field label="Nombre del proyecto" name="nombre" required maxLength={140} /><Field label="Nombre del equipo" name="equipo" required maxLength={100} /><Field label="Estudiante líder" name="lider" required maxLength={120} /><Field label="Asesor" name="asesor" required maxLength={120} /><TextArea label="Descripción de la propuesta" name="descripcion" required maxLength={2500} />{error && <p className="error" role="alert">{error}</p>}<button className="button">Guardar borrador</button></form></Modal>}
    {current && <Modal title={current.nombre} onClose={closeDetail}>
      <dl className="event-meta"><div><dt>Equipo</dt><dd>{current.equipo}</dd></div><div><dt>Líder</dt><dd>{current.lider}</dd></div><div><dt>Asesor</dt><dd>{current.asesor}</dd></div><div><dt>Registro</dt><dd>{dateLabel(current.fecha)}</dd></div><div><dt>Categoría</dt><dd>{current.categoria}</dd></div></dl>
      <p>{current.descripcion}</p><Badge>{current.estatus}</Badge>
      {current.observaciones && <p className="info-box">Observaciones de coordinación: {current.observaciones}</p>}
      {editable && !editing && <div className="form-actions"><button className="button secondary" onClick={() => setEditing(true)}>Editar propuesta</button><button className="button" disabled={busy} onClick={async () => { if (await update('innovation', { ...current, estatus: 'En revisión', estatus_anterior: current.estatus })) { closeDetail(); notify('Propuesta enviada a coordinación.'); } }}>Enviar a revisión</button></div>}
      {editable && editing && <form className="form-stack" data-unsaved="true" onSubmit={saveProposal}>
        <Field label="Nombre del proyecto" name="nombre" defaultValue={current.nombre} required maxLength={140} />
        <Field label="Nombre del equipo" name="equipo" defaultValue={current.equipo} required maxLength={100} />
        <Field label="Estudiante líder" name="lider" defaultValue={current.lider} required maxLength={120} />
        <Field label="Asesor" name="asesor" defaultValue={current.asesor} required maxLength={120} />
        <TextArea label="Descripción de la propuesta" name="descripcion" defaultValue={current.descripcion} required maxLength={2500} />
        <div className="form-actions"><button className="button secondary" value="Borrador" disabled={busy}>Guardar cambios</button><button className="button" value="En revisión" disabled={busy}>Enviar a revisión</button></div>
      </form>}
      {role === 'admin' && ['En revisión', 'Aprobada'].includes(current.estatus) && <form key={`${current.id}-${current.estatus}-${current.etapa}`} className="form-stack" data-unsaved="true" onSubmit={review}>
        <Field label="Etapa" name="etapa" defaultValue={current.etapa}>{['Local', 'Regional', 'Nacional'].filter((stage, i, stages) => i >= stages.indexOf(current.etapa) && i <= stages.indexOf(current.etapa) + 1).map(t => <option key={t}>{t}</option>)}</Field>
        <Field label="Resultado de revisión" name="estatus" defaultValue="Aprobada">{(current.estatus === 'Aprobada' ? ['Aprobada'] : ['Aprobada', 'Correcciones solicitadas', 'Rechazada']).map(t => <option key={t}>{t}</option>)}</Field>
        <TextArea label="Observaciones (obligatorias para correcciones o rechazo)" name="observaciones" defaultValue={current.observaciones || ''} maxLength={5000} />
        <button className="button" disabled={busy}>Guardar seguimiento</button>
      </form>}
      <Panel title="Historial de seguimiento"><Table headings={['Fecha', 'Responsable', 'Estado / etapa', 'Observaciones']} empty={!current.historial?.length}>{(current.historial || []).map((entry, i) => <tr key={i}><td>{new Date(entry.fecha).toLocaleString('es-MX', { timeZone: 'America/Mexico_City' })}</td><td>{entry.nombre}</td><td>{entry.estatus} · {entry.etapa}</td><td>{entry.observaciones || '—'}</td></tr>)}</Table></Panel>
    </Modal>}
  </>;
}

