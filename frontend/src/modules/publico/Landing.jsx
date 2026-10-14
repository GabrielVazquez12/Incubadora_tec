import { Link } from 'react-router-dom';
import Newsletter from './Newsletter.jsx';
import PublicLayout from './PublicLayout.jsx';
import BrandImage from '../../shared/BrandImage.jsx';
import Icon from '../../shared/design/Icon.jsx';
import { Stepper } from '../../shared/portal/ui.jsx';
import './landing.css';

const pillars = [
  ['emprendimiento', 'Emprendimiento', '/incubadora'],
  ['innovacion', 'InnovaTec', '/innovatec'],
  ['vinculacion', 'Vinculación', '/vinculacion'],
  ['eventos', 'Eventos', '/eventos'],
];
const strategy = [
  ['Centralizar', 'Convocatorias, requisitos, fechas, beneficios y registro en un solo sitio.'],
  ['Difundir', 'Información para la comunidad por redes, docentes, coordinadores y salones.'],
  ['Acercar', 'Visitas a salones y orientación para alumnos y docentes.'],
  ['Orientar', 'Información clara sobre los programas, sus requisitos y procesos.'],
  ['Generar interés', 'Noticias, experiencias y contenidos para participar y dar continuidad a los proyectos.'],
];

export default function Landing() {
  return <PublicLayout>
    <section className="enlaces-hero landing-container">
      <BrandImage priority maxWidth={420} sizes="(min-width: 768px) 25vw, 46vw" />
      <div><p className="landing-eyebrow">Tecnológico Nacional de México · Instituto Tecnológico de Saltillo</p><h1>Enlaces<br />Institucionales ITS</h1><p className="brand-motto">Conectando ideas, generando oportunidades</p><p className="landing-lead">Emprendimiento, InnovaTec, vinculación y eventos: una red para orientar tus ideas y acompañar su desarrollo.</p><div className="landing-actions"><Link className="button" to="/registro">Registra tu proyecto</Link><a className="text-link" href="#servicios">Conocer los programas</a></div></div>
    </section>
    <section className="pillars landing-container" aria-label="Pilares institucionales">{pillars.map(([icon, title, to]) => <Link key={to} to={to}><Icon name={icon} /><span>{title}</span></Link>)}</section>
    <section id="servicios" className="programs landing-container"><p className="landing-eyebrow">Nuestros programas</p><h2>Ideas con acompañamiento.<br />Proyectos con continuidad.</h2><div className="program-grid">
      <article><Icon name="emprendimiento" /><h3>Incubadora de Empresas</h3><p>Registro, diagnóstico, asesoría personalizada y seguimiento para ideas y negocios.</p><Link className="button secondary" to="/incubadora">Conocer la Incubadora</Link></article>
      <article><Icon name="innovacion" /><h3>InnovaTec</h3><p>Información del proceso local, participación de equipos y continuidad hacia las etapas regional y nacional.</p><Link className="button secondary" to="/innovatec">Conocer InnovaTec</Link></article>
    </div></section>
    <section id="estrategia" className="strategy-section"><div className="landing-container"><p className="landing-eyebrow">Enlaces Institucionales ITS</p><h2>Una sola red,<br />toda la información.</h2><div className="strategy-grid">{strategy.map(([title, description]) => <article key={title}><h3>{title}</h3><p>{description}</p></article>)}</div></div></section>
    <Newsletter />
    <section id="proceso" className="landing-process"><div className="landing-container"><p className="landing-eyebrow">Empieza con una idea</p><h2>El primer paso está en tus manos.</h2><Stepper horizontal label="Cómo comenzar un proyecto" steps={[{ title: 'Crea tu cuenta', description: 'Regístrate como estudiante ITS o participante externo.' }, { title: 'Presenta tu proyecto', description: 'Completa tu solicitud y comparte la información de tu propuesta.' }, { title: 'Avanza con acompañamiento', description: 'Da seguimiento a la revisión y a las actividades de tu proyecto.' }]} /></div></section>
    <section className="quick-access landing-container" aria-labelledby="quick-access-title"><h2 id="quick-access-title">Tu siguiente paso</h2><div><Link className="text-link" to="/registro">Registra tu proyecto</Link><Link className="text-link" to="/innovatec">Inscríbete a InnovaTec</Link><Link className="text-link" to="/encuestas">Responde la encuesta</Link></div></section>
    <section className="landing-cta landing-container"><div><p className="landing-eyebrow">Enlaces Institucionales ITS</p><h2>¡Tu idea, nuestro apoyo!</h2></div><Link className="button" to="/registro">Crear mi cuenta</Link></section>
  </PublicLayout>;
}
