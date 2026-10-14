import { coordinationRoutes } from './modules/coordinacion/routes';
import { studentRoutes } from './modules/estudiantes/routes';
import { externalRoutes } from './modules/externos/routes';
import { BrowserRouter, Routes, Route, Navigate, Link, useSearchParams, useParams } from 'react-router-dom';
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
import PublicInnova from './modules/innovatec/PublicInnova.jsx';
import CallAdmin from './modules/innovatec/CallAdmin.jsx';
import { Teams, TeamDetail } from './modules/innovatec/Teams.jsx';
import { Talks, Diplomas } from './modules/innovatec/Talks.jsx';
import { PublicIncubation, Dossier, Followups, Indicators, CatalogAdmin } from './modules/incubadora/Incubation.jsx';
import { usePortal } from './shared/portal/PortalContext.jsx';
import { Skeleton } from './shared/portal/ui.jsx';
import { rolePaths } from './shared/portal/data.js';
import './shared/portal/portal.css';

function InnovationLayout({ preview }) {
  const [params] = useSearchParams();
  const role = preview ? (params.get('rol') === 'admin' ? 'admin' : 'estudiante') : localStorage.getItem('rol');
  return <PortalLayout role={role} preview={preview} innovation />;
}

const actorRoutes = { admin: coordinationRoutes, estudiante: studentRoutes, externo: externalRoutes };

function InnovaAlias({ section = 'equipos' }) {
  const { user } = usePortal(), { id } = useParams();
  if (!user) return <Skeleton />;
  const path = user.rol === 'admin' ? `/coordinador/innovatec/${section}` : '/emprendedor/proyectos/innovatec/equipos';
  return <Navigate replace to={`${path}${id ? `/${id}` : ''}`} />;
}

function IncubationAlias({ section = 'proyectos' }) {
  const { user } = usePortal(), { id } = useParams();
  if (!user) return <Skeleton />;
  const root = user.rol === 'admin' ? '/coordinador' : '/emprendedor';
  const path = section === 'proyectos' ? `${user.rol === 'admin' ? 'seguimiento' : 'proyectos'}${id ? `/${id}` : ''}` : section === 'indicadores' ? 'reportes/indicadores' : `seguimiento/${section === 'inactivos' ? 'inactivos' : 'semana'}`;
  return <Navigate replace to={`${root}/${path}`} />;
}

function portalRoutes(role, preview) {
  const base = `${preview ? '/vista-previa' : ''}/${rolePaths[role]}`;
  const layout = <PortalLayout role={role} preview={preview} />;
  return <Route key={base} path={base} element={preview ? layout : <RutaProtegida rolesPermitidos={[role]}>{layout}</RutaProtegida>}>
    <Route index element={<Navigate to="inicio" replace />} />
    <Route path="inicio" element={<Home />} />
    <Route path="boletin" element={<CommunityNewsletter />} />
    <Route path="pagos" element={<Payments />} />
    {actorRoutes[role].map(([path, element]) => <Route key={path} path={path} element={element} />)}
    {role === 'estudiante' && <Route path="proyectos/innovatec/equipos" element={<Teams />} />}
    {role === 'estudiante' && <Route path="proyectos/innovatec/equipos/:id" element={<TeamDetail />} />}
    {role === 'admin' && <Route path="innovatec" element={<Teams />} />}
    {role === 'admin' && <Route path="innovatec/convocatoria" element={<CallAdmin />} />}
    {role === 'admin' && <Route path="innovatec/equipos" element={<Teams />} />}
    {role === 'admin' && <Route path="innovatec/equipos/:id" element={<TeamDetail />} />}
    {role === 'admin' && <Route path="innovatec/platicas" element={<Talks />} />}
    {role === 'admin' && <Route path="innovatec/diplomas" element={<Diplomas />} />}
    {role === 'admin' && <Route path="innovatec/seguimiento" element={<Teams seguimiento />} />}
    {role === 'admin' && <Route path="catalogo" element={<CatalogAdmin />} />}
    {role === 'admin' && <Route path="catalogo/hitos" element={<CatalogAdmin hitos />} />}
    {role === 'admin' && <Route path="reportes/indicadores" element={<Indicators />} />}
    {role === 'admin' && ['semana', 'vencidos', 'inactivos'].map(view => <Route key={view} path={`seguimiento/${view}`} element={<Followups view={view} />} />)}
    {role === 'admin' && [
      ['difusion', 'Difusión'], ['difusion/visitas', 'Visitas a salones'], ['difusion/plantillas', 'Plantillas de mensajes'],
      ['encuestas', 'Encuestas'], ['encuestas/resultados', 'Resultados de encuestas'],
    ].map(([path, title]) => <Route key={path} path={path} element={<PendingModule title={title} />} />)}
  </Route>;
}

export function AppRoutes({ enablePreview = false }) {
  return <Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/login" element={<Login />} />
    <Route path="/registro" element={<Registro />} />
    {['vinculacion', 'eventos', 'contacto', 'encuestas'].map(section => <Route key={section} path={`/${section}`} element={<PublicPage section={section} />} />)}
    <Route path="/incubadora" element={<PublicIncubation />} />
    <Route path="/incubadora/registro" element={<PublicIncubation section="registro" />} />
    <Route path="/incubadora/catalogo" element={<PublicIncubation section="catalogo" />} />
    <Route path="/incubadora/catalogo/:id" element={<PublicIncubation section="catalogo" />} />
    <Route path="/incubadora/proyectos" element={<RutaProtegida rolesPermitidos={['admin', 'estudiante']}><IncubationAlias /></RutaProtegida>} />
    <Route path="/incubadora/proyectos/:id" element={<RutaProtegida rolesPermitidos={['admin', 'estudiante']}><IncubationAlias /></RutaProtegida>} />
    <Route path="/incubadora/proyectos/:id/bitacora" element={<RutaProtegida rolesPermitidos={['admin', 'estudiante']}><IncubationAlias /></RutaProtegida>} />
    {['seguimientos', 'inactivos', 'indicadores'].map(section => <Route key={section} path={`/incubadora/${section}`} element={<RutaProtegida rolesPermitidos={['admin']}><IncubationAlias section={section} /></RutaProtegida>} />)}
    <Route path="/innovatec" element={<PublicInnova section="proceso" />} />
    {['proceso', 'convocatoria', 'inscripcion', 'platicas'].map(section => <Route key={section} path={`/innovatec/${section}`} element={<PublicInnova section={section} />} />)}
    <Route path="/innovatec/equipos" element={<RutaProtegida rolesPermitidos={['admin', 'estudiante']}><InnovaAlias /></RutaProtegida>} />
    <Route path="/innovatec/equipos/:id" element={<RutaProtegida rolesPermitidos={['admin', 'estudiante']}><InnovaAlias /></RutaProtegida>} />
    {['diplomas', 'seguimiento'].map(section => <Route key={section} path={`/innovatec/${section}`} element={<RutaProtegida rolesPermitidos={['admin']}><InnovaAlias section={section} /></RutaProtegida>} />)}
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
