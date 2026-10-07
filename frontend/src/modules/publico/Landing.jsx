import Newsletter from './Newsletter.jsx';
import { Link } from 'react-router-dom';
import InstitutionalBrand from '../../shared/InstitutionalBrand.jsx';
import './landing.css';

const services = [
  ['01', 'Incubación de proyectos', 'Dale estructura a tu idea, evalúa su factibilidad y construye tu plan de negocio.', '/registro'],
  ['02', 'Asesoría y tutorías', 'Encuentra acompañamiento para los retos legales, administrativos y financieros de tu proyecto.', '/login'],
  ['03', 'Eventos y formación', 'Explora talleres y actividades para fortalecer tus habilidades de emprendimiento.', '/login'],
  ['04', 'InnovaTecNM', 'Conoce los módulos de innovación y prepara tu propuesta para participar.', '/login'],
];

export default function Landing() {
  return <div className="landing">
    <a className="skip-link" href="#contenido">Saltar al contenido</a>
    <div className="landing-institution">Instituto Tecnológico de Saltillo <span>La Técnica por la Grandeza de México</span></div>
    <header className="landing-header"><div className="landing-container landing-header-row">
      <Link to="/" aria-label="Incubadora ITS · Inicio"><InstitutionalBrand /></Link>
      <nav aria-label="Navegación principal"><a href="#actualidad">Noticias y eventos</a><a href="#servicios">Servicios</a><a href="#proceso">Cómo empezar</a><a href="#contacto">Contacto</a></nav>
      <Link to="/login" className="landing-login">Iniciar sesión ↗</Link>
    </div></header>
    <main id="contenido"><Newsletter />
      <section className="landing-hero landing-container">
        <div><p className="landing-eyebrow">Centro de Emprendurismo y Negocios</p><h2>Tu idea tiene futuro.<br /><em>Construyámoslo.</em></h2><p className="landing-lead">Transforma tu talento en un proyecto con propósito. En la Incubadora ITS te acompañamos desde la primera idea hasta el desarrollo de tu negocio.</p><div className="landing-actions"><Link className="button" to="/registro">Comenzar mi proyecto →</Link><a className="landing-text-link" href="#servicios">Conocer los servicios ↓</a></div><p className="landing-hero-note">Emprendimiento · Innovación · Comunidad ITS</p></div>
        <div className="landing-feature"><div className="landing-feature-top"><span>DE LA IDEA A LA ACCIÓN</span><span aria-hidden="true">↗</span></div><h2>Un espacio para<br />hacer que suceda.</h2><p>Conocimiento, acompañamiento y herramientas para avanzar con claridad.</p><div className="landing-path">{['Explora tu idea', 'Desarrolla tu proyecto', 'Impulsa tu negocio'].map((title, i) => <div key={title}><span>0{i + 1}</span><strong>{title}</strong></div>)}</div><div className="landing-feature-bottom">INCUBADORA ITS <span>Saltillo, Coahuila</span></div></div>
      </section>
      <section id="servicios" className="landing-services landing-container"><div className="landing-section-heading"><div><p className="landing-eyebrow">Acompañamiento que suma</p><h2>Herramientas para tu siguiente paso.</h2></div><p>Explora lo que puedes hacer en el portal y encuentra el apoyo que necesita tu proyecto.</p></div><div className="landing-service-grid">{services.map(([number, title, description, href]) => <Link className="landing-service" to={href} key={number}><span className="landing-service-number">{number}</span><h3>{title}</h3><p>{description}</p><span className="landing-service-link">Acceder al servicio <span aria-hidden="true">↗</span></span></Link>)}</div><p className="landing-demo-note">Regístrate para presentar tu proyecto o inicia sesión para consultar los servicios de tu cuenta.</p></section>
      <section id="proceso" className="landing-process"><div className="landing-container"><p className="landing-eyebrow">Empieza con una idea</p><h2>El primer paso está en tus manos.</h2><div className="landing-steps">{[['Crea tu cuenta', 'Regístrate como estudiante ITS o participante externo.'], ['Presenta tu proyecto', 'Completa tu solicitud y comparte la información de tu propuesta.'], ['Avanza con acompañamiento', 'Da seguimiento a la revisión y a las actividades de tu proyecto.']].map(([title, text], i) => <div key={title}><span>0{i + 1}</span><h3>{title}</h3><p>{text}</p></div>)}</div></div></section>
      <section className="landing-cta landing-container"><div><p className="landing-eyebrow">Talento con propósito</p><h2>Las grandes ideas empiezan<br />con alguien como tú.</h2></div><Link className="button" to="/registro">Crear mi cuenta →</Link></section>
    </main>
    <footer id="contacto" className="landing-footer"><div className="landing-container"><div className="landing-footer-grid"><div><InstitutionalBrand /><p>Centro de Emprendurismo y Negocios<br />Instituto Tecnológico de Saltillo</p></div><div><h2>Visítanos</h2><p>Blvd. Venustiano Carranza #2400<br />Col. Tecnológico, Saltillo, Coahuila</p><a href="https://saltillo.tecnm.mx/" target="_blank" rel="noreferrer">Sitio institucional ↗</a></div><div><h2>Tu espacio de emprendimiento</h2><Link to="/login">Acceder al portal</Link><Link to="/registro">Registrarme</Link><a href="#servicios">Explorar servicios</a></div></div><div className="landing-footer-bottom"><span>ITS · Incubadora en Línea</span><span>Emprendimiento · Innovación · Comunidad</span></div></div></footer>
  </div>;
}
