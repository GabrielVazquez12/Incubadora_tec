import { Link } from 'react-router-dom';
import BrandImage from './BrandImage.jsx';
import { useRemote } from '../modules/innovatec/api.js';

export default function InstitutionalFooter({ navigation = true }) {
  const config = useRemote('/public/enlaces/configuracion');
  const contacts = config.data?.contactos || {};
  return <footer className="enlaces-footer" id="contacto"><div className="enlaces-footer-inner">
    <div><BrandImage maxWidth={180} sizes="180px" /><p className="brand-motto">Conectando ideas, generando oportunidades</p></div>
    {navigation && <nav aria-label="Secciones institucionales"><h2>Enlaces Institucionales ITS</h2><Link to="/">Inicio</Link><Link to="/incubadora">Incubadora de Empresas</Link><Link to="/innovatec">InnovaTec</Link><Link to="/vinculacion">Vinculación</Link><Link to="/eventos">Eventos</Link><Link to="/contacto">Contacto</Link></nav>}
    <div><h2>Contacto institucional</h2><p>Instituto Tecnológico de Saltillo</p>{config.error && <p role="alert">{config.error}</p>}<p>{contacts.correo || '[Por definir: correo de contacto]'}</p><p>{contacts.telefono || '[Por definir: teléfono]'}</p><p>{contacts.horario || '[Por definir: horario de atención]'}</p><Link to="/aviso-de-privacidad">Aviso de privacidad</Link><h2>Redes institucionales</h2><ul className="social-placeholders">{['Instagram', 'TikTok', 'WhatsApp', 'Facebook'].map(network => <li key={network}>{contacts[network.toLowerCase()] ? <a href={contacts[network.toLowerCase()]} target="_blank" rel="noopener noreferrer">{network}</a> : <>[Por definir: {network}]</>}</li>)}</ul></div>
  </div><div className="enlaces-footer-bottom">Enlaces Institucionales ITS · Tecnológico Nacional de México · Instituto Tecnológico de Saltillo</div></footer>;
}
