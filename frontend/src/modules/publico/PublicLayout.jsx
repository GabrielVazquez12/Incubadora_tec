import { Link } from 'react-router-dom';
import Navigation from '../../shared/design/Navigation.jsx';
import InstitutionalFooter from '../../shared/InstitutionalFooter.jsx';

const items = [['/', 'Inicio'], ['/incubadora', 'Incubadora de Empresas'], ['/innovatec', 'InnovaTec'], ['/vinculacion', 'Vinculación'], ['/eventos', 'Eventos'], ['/contacto', 'Contacto']].map(([to, label]) => ({ to, label, end: to === '/' }));

export default function PublicLayout({ children }) {
  return <div className="landing"><a className="skip-link" href="#contenido">Saltar al contenido</a><Navigation publicSite home="/" items={items} account={<Link className="button secondary" to="/login">Iniciar sesión</Link>} /><main id="contenido" className="public-main">{children}</main><InstitutionalFooter /></div>;
}
