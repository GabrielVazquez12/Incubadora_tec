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
  return <PublicLayout><div className="editorial-home">
    <nav className="editorial-sections landing-container" aria-label="En esta página"><a href="#actualidad">Newsletter</a><a href="#mision-vision">Misión y visión</a><a href="#contacto-vinculacion">Contacto</a><a href="#ubicaciones">Ubicación</a></nav>
    <section className="editorial-hero">
      <div className="editorial-hero-copy"><p className="editorial-context">Emprendimiento e innovación en el ITS</p><h1>Aquí empieza<br />tu próxima idea.</h1><p className="editorial-lead">Una red de programas para orientar tu proyecto, conectar con otras personas y acompañar su desarrollo.</p><div className="landing-actions"><Link className="button" to="/incubadora/registro">Registrar mi proyecto</Link><a href="#servicios">Explorar los programas</a></div></div>
      <div className="editorial-poster"><BrandImage priority maxWidth={260} sizes="(min-width: 768px) 250px, 46vw" /><p>Enlaces Institucionales ITS<br /><span>Conectando ideas, generando oportunidades.</span></p></div>
    </section>
    <section className="pillars landing-container" aria-label="Pilares institucionales">{pillars.map(([icon, title, to]) => <Link key={to} to={to}><Icon name={icon} /><span>{title}</span></Link>)}</section>
    <section id="servicios" className="programs landing-container"><p className="landing-eyebrow">Nuestros programas</p><h2>Elige el camino<br />de tu proyecto.</h2><div className="program-grid">
      <article><Icon name="emprendimiento" /><h3>Incubadora de Empresas</h3><p>Registro, diagnóstico, asesoría personalizada y seguimiento para ideas y negocios.</p><Link className="button secondary" to="/incubadora">Conocer la Incubadora</Link></article>
      <article><Icon name="innovacion" /><h3>InnovaTec</h3><p>Información del proceso local, participación de equipos y continuidad hacia las etapas regional y nacional.</p><Link className="button secondary" to="/innovatec">Conocer InnovaTec</Link></article>
    </div></section>
    <section id="estrategia" className="strategy-section"><div className="landing-container"><p className="landing-eyebrow">Enlaces Institucionales ITS</p><h2>Una sola red,<br />toda la información.</h2><div className="strategy-grid">{strategy.map(([title, description]) => <article key={title}><h3>{title}</h3><p>{description}</p></article>)}</div></div></section>
    <Newsletter defer />
    <section id="proceso" className="landing-process"><div className="landing-container"><p className="landing-eyebrow">Empieza con una idea</p><h2>El primer paso está en tus manos.</h2><Stepper horizontal label="Cómo comenzar un proyecto" steps={[{ title: 'Crea tu cuenta', description: 'Regístrate como estudiante ITS o participante externo.' }, { title: 'Presenta tu proyecto', description: 'Completa tu solicitud y comparte la información de tu propuesta.' }, { title: 'Avanza con acompañamiento', description: 'Da seguimiento a la revisión y a las actividades de tu proyecto.' }]} /></div></section>
    <section className="quick-access landing-container" aria-labelledby="quick-access-title"><h2 id="quick-access-title">Tu siguiente paso</h2><div><Link className="text-link" to="/incubadora/registro">Registra tu proyecto</Link><Link className="text-link" to="/innovatec/inscripcion">Inscríbete a InnovaTec</Link><Link className="text-link" to="/encuestas">Responde la encuesta</Link><Link className="text-link" to="/difusion">Consulta la difusión institucional</Link></div></section>
<section className="purpose" id="mision-vision">
          <div className="landing-container">
            <div className="section-intro">
              <div>
                <p className="section-kicker">Instituto Tecnológico de Saltillo</p>
                <h2>Una comunidad.<br />Un propósito compartido.</h2>
              </div>
              <p>La misión y visión institucionales dan contexto a nuestro trabajo de formación, innovación y vinculación.</p>
            </div>
            <div className="purpose-grid">
              <article>
                <h3>Misión</h3>
                <p>Formar profesionales integrales mediante educación tecnológica de calidad, con responsabilidad social y conocimientos científicos e innovadores que aporten al desarrollo sustentable de México.</p>
              </article>
              <article>
                <h3>Visión</h3>
                <p>Alcanzar reconocimiento nacional e internacional por la calidad académica, los servicios y los procesos institucionales, así como por egresados competitivos que contribuyan al desarrollo del país.</p>
              </article>
            </div>
            <p className="source-note">Síntesis de la misión y visión del ITS. <a href="https://saltillo.tecnm.mx/misionyvision" target="_blank" rel="noopener">Consultar el texto oficial completo<span className="sr-only"> (abre otra pestaña)</span> →</a>
            </p>
          </div>
        </section>
        <section className="contact-section landing-container" id="contacto-vinculacion">
          <div className="section-intro">
            <div>
              <p className="section-kicker">Gestión Tecnológica y Vinculación</p>
              <h2>Conversemos sobre<br />tu siguiente paso.</h2>
            </div>
            <p>Orientación institucional para conectar tu proyecto con los programas del ITS.</p>
          </div>
          <div className="contact-grid">
            <article>
              <h3>Contacto de Vinculación</h3>
              <p>Departamento de Gestión Tecnológica y Vinculación</p>
              <a className="contact-phone" href="tel:+528442889460">844 288 9460</a>
              <p>Extensión 1010</p>
              <p>Para confirmar el correo y la persona responsable, consulta el directorio institucional.</p>
              <a className="text-link" href="https://saltillo.tecnm.mx/directorio" target="_blank" rel="noopener">Ver directorio oficial<span className="sr-only"> (abre otra pestaña)</span> →</a>
            </article>
            <article className="location-panel" id="ubicaciones">
              <p className="section-kicker">Ubicación · Campus ITS</p>
              <h3>Visítanos en Saltillo</h3>
              <address>Blvd. Venustiano Carranza #2400<br />Col. Tecnológico, C.P. 25280<br />Saltillo, Coahuila, México</address>
              <p>Confirma por teléfono el edificio, acceso y horario de atención de Vinculación antes de acudir.</p>
              <a className="button outline" href="https://www.google.com/maps/search/?api=1&amp;query=Instituto+Tecnologico+de+Saltillo+Venustiano+Carranza+2400" target="_blank" rel="noopener">Cómo llegar al ITS<span className="sr-only"> (abre Google Maps en otra pestaña)</span> ↗</a>
              <p className="source-note">
                <a href="https://saltillo.tecnm.mx/" target="_blank" rel="noopener">Dirección publicada por el ITS<span className="sr-only"> (abre otra pestaña)</span>
                </a>
              </p>
            </article>
          </div>
        </section>

    <section className="landing-cta landing-container"><div><p className="landing-eyebrow">Enlaces Institucionales ITS</p><h2>¡Tu idea, nuestro apoyo!</h2></div><Link className="button" to="/registro">Crear mi cuenta</Link></section>
  </div></PublicLayout>;
}
