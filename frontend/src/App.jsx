import { coordinationRoutes } from './modules/coordinacion/routes';
import { studentRoutes } from './modules/estudiantes/routes';
import { externalRoutes } from './modules/externos/routes';
import { BrowserRouter, Routes, Route, Navigate, Link, useSearchParams } from 'react-router-dom';
import RutaProtegida from './modules/autenticacion/RutaProtegida.jsx';
import Landing from './modules/publico/Landing.jsx';
import PublicPage from './modules/publico/PublicPages.jsx';
import PendingModule from './shared/design/PendingModule.jsx';
import Login from './modules/autenticacion/Login.jsx';
import Registro from './modules/autenticacion/Registro.jsx';
import { PortalProvider } from './shared/portal/PortalContext.jsx';
import PortalLayout from './shared/portal/PortalLayout.jsx';
import Home from './shared/portal/Home.jsx';
import CommunityNewsletter from './shared/portal/CommunityNewsletter.jsx';
import { Payments } from './shared/events/Payments.jsx';
import Innovation from './modules/innovacion/Innovation.jsx';
import { rolePaths } from './shared/portal/data.js';
import './shared/portal/portal.css';

function InnovationLayout({ preview }) {
  const [params] = useSearchParams();
  const role = preview ? (params.get('rol') === 'admin' ? 'admin' : 'estudiante') : localStorage.getItem('rol');
  return <PortalLayout role={role} preview={preview} innovation />;
}

const actorRoutes = { admin: coordinationRoutes, estudiante: studentRoutes, externo: externalRoutes };

function portalRoutes(role, preview) {
  const base = `${preview ? '/vista-previa' : ''}/${rolePaths[role]}`;
  const layout = <PortalLayout role={role} preview={preview} />;
  return <Route key={base} path={base} element={preview ? layout : <RutaProtegida rolesPermitidos={[role]}>{layout}</RutaProtegida>}>
    <Route index element={<Navigate to="inicio" replace />} />
    <Route path="inicio" element={<Home />} />
    <Route path="boletin" element={<CommunityNewsletter />} />
    <Route path="pagos" element={<Payments />} />
    {actorRoutes[role].map(([path, element]) => <Route key={path} path={path} element={element} />)}
    {role === 'admin' && [
      ['difusion', 'Difusión'], ['difusion/visitas', 'Visitas a salones'], ['difusion/plantillas', 'Plantillas de mensajes'],
      ['reportes/indicadores', 'Indicadores'], ['seguimiento/semana', 'Seguimientos de la semana'], ['seguimiento/vencidos', 'Seguimientos vencidos'], ['seguimiento/inactivos', 'Inactivos'],
      ['encuestas', 'Encuestas'], ['encuestas/resultados', 'Resultados de encuestas'], ['catalogo', 'Catálogo de servicios'], ['catalogo/hitos', 'Hitos comunes'],
      ['innovatec', 'Gestión InnovaTec'], ['innovatec/convocatoria', 'Convocatoria InnovaTec'], ['innovatec/equipos', 'Equipos InnovaTec'], ['innovatec/platicas', 'Pláticas informativas'], ['innovatec/diplomas', 'Diplomas'], ['innovatec/seguimiento', 'Seguimiento de equipos'],
    ].map(([path, title]) => <Route key={path} path={path} element={<PendingModule title={title} />} />)}
  </Route>;
}

export function AppRoutes({ enablePreview = false }) {
  return <Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/login" element={<Login />} />
    <Route path="/registro" element={<Registro />} />
    {['incubadora', 'innovatec', 'vinculacion', 'eventos', 'contacto', 'encuestas'].map(section => <Route key={section} path={`/${section}`} element={<PublicPage section={section} />} />)}
    <Route path="/aviso-de-privacidad" element={<PublicPage section="privacidad" />} />
    {enablePreview && <Route path="/vista-previa" element={<Navigate to="/vista-previa/emprendedor/inicio" replace />} />}
    {(enablePreview ? [false, true] : [false]).flatMap(preview => ['estudiante', 'admin', 'externo'].map(role => portalRoutes(role, preview)))}
    {(enablePreview ? [false, true] : [false]).map(preview => <Route key={`innovation-${preview}`} path={`${preview ? '/vista-previa' : ''}/innovatecnm`} element={preview ? <InnovationLayout preview /> : <RutaProtegida rolesPermitidos={['admin', 'estudiante']}><InnovationLayout /></RutaProtegida>}>
      <Route index element={<Navigate to="inicio" replace />} />
      {['inicio', 'certamen', 'hackatec', 'innobotica', 'innovaccion', 'retos', 'registros'].map(section => <Route key={section} path={section} element={<Innovation section={section} />} />)}
    </Route>)}
    <Route path="*" element={<div className="not-found"><h1>Página no encontrada</h1><p>La dirección no corresponde a una pantalla disponible.</p><Link className="button" to="/">Volver al inicio</Link></div>} />
  </Routes>;
}

export default function App() {
  return <BrowserRouter><PortalProvider><AppRoutes /></PortalProvider></BrowserRouter>;
}
