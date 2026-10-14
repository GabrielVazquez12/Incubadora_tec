import { Link } from 'react-router-dom';
export default function AccessDenied() {
  return <section className="panel" aria-labelledby="access-denied"><h1 id="access-denied">Acceso restringido</h1><p>Tu cuenta no dispone del permiso necesario para esta sección.</p><Link className="button secondary" to="/">Volver al inicio</Link></section>;
}
