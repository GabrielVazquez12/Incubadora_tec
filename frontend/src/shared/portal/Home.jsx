import { Link } from 'react-router-dom';
import Newsletter from '../../modules/publico/Newsletter.jsx';
import BrandImage from '../BrandImage.jsx';
import { closed } from '../events/helpers.js';
import { hasStarted } from './schedule.js';
import { usePortal } from './PortalContext.jsx';
import { usePortalRoute } from './PortalLayout.jsx';
import { demoPeople, dateLabel, roleNames } from './data.js';
import { Badge, Heading, Panel, Progress, Stats } from './ui.jsx';

export default function Home() {
  const { data, user, preview } = usePortal();
  const { role, base, userId } = usePortalRoute();
  if (role === 'admin' || role === 'estudiante') {
    const name = preview ? demoPeople[role] : user?.nombre || '';
    return <section className="portal-welcome" aria-labelledby="welcome-title"><h1 id="welcome-title">{`Bienvenido(a), ${name}`}</h1><p className="welcome-role">{roleNames[role]}</p><BrandImage priority maxWidth={420} /><p className="brand-motto">Conectando ideas, generando oportunidades</p></section>;
  }
  const projects = data.projects.filter(p => role === 'admin' || p.owner === userId || data.members?.some(m => m.proyecto_id === p.id && m.usuario_id === userId));
  const project = projects[0];
  const modules = [
    ['eventos', '01', 'Eventos', 'Conoce e inscríbete a las actividades de la incubadora.'], ['solicitud', '02', 'Solicitar ingreso', 'Cuéntanos tu idea y comienza tu camino como emprendedor.'], ['inscripciones', '03', 'Mis inscripciones', 'Consulta tus actividades y el estado de tu registro.'], ['pagos', '04', 'Mis pagos', 'Revisa tus pagos y comprobantes.'],
  ];
  return <><Heading eyebrow={role === 'admin' ? 'COORDINACIÓN / INICIO' : 'TU ESPACIO DE EMPRENDIMIENTO'} title={role === 'admin' ? 'Panel de coordinación' : `Hola, ${(preview ? demoPeople[role] : user?.nombre || '').split(' ')[0]}`} description={role === 'admin' ? 'Una vista de tu comunidad y las herramientas para acompañarla.' : 'Cada paso acerca tu idea a convertirse en una empresa.'} />
    {role !== 'externo' && <Stats items={role === 'admin' ? [['Proyectos', projects.length], ['Emprendedores', data.users.filter(u => u.rol === 'estudiante').length], ['Eventos activos', data.events.filter(e => !closed(e)).length], ['Progreso promedio', `${Math.round(projects.reduce((sum, p) => sum + p.progreso, 0) / (projects.length || 1))}%`]] : [['Progreso del proyecto', `${project?.progreso || 0}%`], ['Tareas pendientes', data.tasks.filter(t => projects.some(p => p.id === t.project) && t.estatus === 'Pendiente').length], ['Tutorías próximas', data.appointments.filter(a => { const slot = data.slots.find(s => s.id === a.slot); return a.user === userId && a.estatus === 'Confirmada' && slot && !hasStarted(slot.fecha, slot.fin); }).length], ['Eventos inscritos', data.registrations.filter(r => r.user === userId && r.estatus === 'Confirmada').length]]} />}
    <Newsletter portalBase={base} compact />
    <div className="module-grid">{modules.map(([path, number, title, description]) => <Link className="module-card" key={path} to={`${base}/${path}`}><span className="module-number">{number}</span><h2>{title}</h2><p>{description}</p><span className="module-arrow" aria-hidden="true">↗</span></Link>)}</div>
    <div className="two-columns"><Panel title={role === 'externo' ? 'Tu próxima oportunidad' : 'Continúa donde te quedaste'}>{role === 'externo' ? <><p>¿Tienes una idea de negocio? La incubadora te acompaña a convertirla en un proyecto.</p><Link className="button secondary" to={`${base}/solicitud`}>Conocer el proceso →</Link></> : project ? <><div className="row between"><h3>{project.nombre}</h3><Badge>{project.estatus}</Badge></div><p className="muted">{project.descripcion}</p><Progress value={project.progreso} /><Link className="text-link" to={`${base}/${role === 'admin' ? 'seguimiento' : 'proyectos'}/${project.id}`}>Ver proyecto →</Link></> : <p>Aquí verás el seguimiento de tus proyectos.</p>}</Panel><Panel title="En la agenda"><div className="agenda-list">{data.events.filter(e => !closed(e)).sort((a, b) => `${a.fecha}T${a.hora}`.localeCompare(`${b.fecha}T${b.hora}`)).slice(0, 3).map(event => <Link key={event.id} to={`${base}/eventos`}><span className="date-tile">{event.fecha.slice(8)}<small>{new Date(event.fecha + 'T12:00:00').toLocaleDateString('es-MX', { month: 'short' })}</small></span><div><strong>{event.nombre}</strong><small>{event.tipo} · {dateLabel(event.fecha)}</small></div><span>→</span></Link>)}</div></Panel></div>
  </>;
}
