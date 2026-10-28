import { Suspense } from 'react';
import { lazyPage, PageBoundary } from './shared/portal/lazyPage.jsx';
import AccessDenied from './shared/design/AccessDenied.jsx';
import { coordinationRoutes } from './modules/coordinacion/routes';
import { studentRoutes } from './modules/estudiantes/routes';
import { externalRoutes } from './modules/externos/routes';
import { BrowserRouter, Routes, Route, Navigate, Link, useSearchParams, useParams, useLocation } from 'react-router-dom';
import RutaProtegida from './modules/autenticacion/RutaProtegida.jsx';
import Landing from './modules/publico/Landing.jsx';
import Seo from './shared/design/Seo.jsx';
import { PortalProvider } from './shared/portal/PortalContext.jsx';
import { usePortal } from './shared/portal/PortalContext.jsx';
import { Skeleton } from './shared/portal/ui.jsx';
import { rolePaths } from './shared/portal/data.js';
import './shared/portal/portal.css';

const OutreachAdmin = lazyPage(() => import('./modules/difusion/Outreach.jsx'), 'OutreachAdmin');
const ContactAdmin = lazyPage(() => import('./modules/difusion/Outreach.jsx'), 'ContactAdmin');
const PublicContact = lazyPage(() => import('./modules/difusion/Outreach.jsx'), 'PublicContact');
const PublicOutreach = lazyPage(() => import('./modules/difusion/Outreach.jsx'), 'PublicOutreach');
const PublicEvents = lazyPage(() => import('./modules/difusion/Outreach.jsx'), 'PublicEvents');
const Login = lazyPage(() => import('./modules/autenticacion/Login.jsx'), 'default');
const Registro = lazyPage(() => import('./modules/autenticacion/Registro.jsx'), 'default');
const PortalLayout = lazyPage(() => import('./shared/portal/PortalLayout.jsx'), 'default');
const Home = lazyPage(() => import('./shared/portal/Home.jsx'), 'default');
const CommunityNewsletter = lazyPage(() => import('./shared/portal/CommunityNewsletter.jsx'), 'default');
const Payments = lazyPage(() => import('./shared/events/Payments.jsx'), 'Payments');
const Innovation = lazyPage(() => import('./modules/innovacion/Innovation.jsx'), 'default');
const PublicInnova = lazyPage(() => import('./modules/innovatec/PublicInnova.jsx'), 'default');
const CallAdmin = lazyPage(() => import('./modules/innovatec/CallAdmin.jsx'), 'default');
const Teams = lazyPage(() => import('./modules/innovatec/Teams.jsx'), 'Teams');
const TeamDetail = lazyPage(() => import('./modules/innovatec/Teams.jsx'), 'TeamDetail');
const Talks = lazyPage(() => import('./modules/innovatec/Talks.jsx'), 'Talks');
const Diplomas = lazyPage(() => import('./modules/innovatec/Talks.jsx'), 'Diplomas');
const PublicIncubation = lazyPage(() => import('./modules/incubadora/Incubation.jsx'), 'PublicIncubation');
const Dossier = lazyPage(() => import('./modules/incubadora/Incubation.jsx'), 'Dossier');
const Followups = lazyPage(() => import('./modules/incubadora/Incubation.jsx'), 'Followups');
const Indicators = lazyPage(() => import('./modules/incubadora/Incubation.jsx'), 'Indicators');
const CatalogAdmin = lazyPage(() => import('./modules/incubadora/Incubation.jsx'), 'CatalogAdmin');
const PublicSurveys = lazyPage(() => import('./modules/encuestas/Surveys.jsx'), 'PublicSurveys');
const SurveyAdmin = lazyPage(() => import('./modules/encuestas/Surveys.jsx'), 'SurveyAdmin');

const Governance = lazyPage(() => import('./modules/gobierno/Governance.jsx'));
const Advisor = lazyPage(() => import('./modules/gobierno/Advisor.jsx'));

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
    {role !== 'admin' && ['', '/:id'].map(suffix => <Route key={suffix} path={`asesoria${suffix}`} element={<RutaProtegida perfilesPermitidos={['asesor']}><Suspense fallback={<Skeleton />}><Advisor /></Suspense></RutaProtegida>} />)}
    {role === 'admin' && ['accesos', 'auditoria'].map(view => <Route key={view} path={`roles/${view}`} element={<RutaProtegida requiereAdministracion><Suspense fallback={<Skeleton />}><Governance key={view} audit={view === 'auditoria'} /></Suspense></RutaProtegida>} />)}
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
    {role === 'admin' && <Route path="encuestas" element={<SurveyAdmin />} />}
    {role === 'admin' && <Route path="encuestas/resultados" element={<SurveyAdmin results />} />}
    {role === 'admin' && ['semana', 'vencidos', 'inactivos'].map(view => <Route key={view} path={`seguimiento/${view}`} element={<Followups view={view} />} />)}
    {role === 'admin' && [
      ['difusion', 'piezas'], ['difusion/visitas', 'visitas'], ['difusion/plantillas', 'plantillas'], ['difusion/preguntas', 'preguntas'], ['eventos/fichas', 'fichas'],
    ].map(([path, collection]) => <Route key={path} path={path} element={<OutreachAdmin key={collection} collection={collection} />} />)}
    {role === 'admin' && <Route path="difusion/contacto" element={<ContactAdmin />} />}
  </Route>;
}

export function AppRoutes({ enablePreview = false }) {
  const { pathname } = useLocation();
  return <PageBoundary resetKey={pathname}><Suspense fallback={<div data-route-loading="true"><Skeleton label="Cargando pantalla…" /></div>}><Routes>
    <Route path="/" element={<Landing />} />
    <Route path="/403" element={<AccessDenied />} />
    <Route path="/login" element={<Login />} />
    <Route path="/registro" element={<Registro />} />
    {['vinculacion', 'contacto'].map(section => <Route key={section} path={`/${section}`} element={<PublicContact key={section} section={section} />} />)}
    <Route path="/difusion" element={<PublicOutreach />} />
    <Route path="/eventos" element={<PublicEvents />} />
    <Route path="/eventos/:id" element={<PublicEvents />} />
    <Route path="/encuestas" element={<PublicSurveys />} />
    <Route path="/encuestas/:id" element={<PublicSurveys />} />
    <Route path="/admin/encuestas" element={<RutaProtegida rolesPermitidos={['admin']}><Navigate replace to="/coordinador/encuestas" /></RutaProtegida>} />
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
    <Route path="/aviso-de-privacidad" element={<PublicContact section="privacidad" />} />
    {enablePreview && <Route path="/vista-previa" element={<Navigate to="/vista-previa/emprendedor/inicio" replace />} />}
    {(enablePreview ? [false, true] : [false]).flatMap(preview => ['estudiante', 'admin', 'externo'].map(role => portalRoutes(role, preview)))}
    {(enablePreview ? [false, true] : [false]).map(preview => <Route key={`innovation-${preview}`} path={`${preview ? '/vista-previa' : ''}/innovatecnm`} element={preview ? <InnovationLayout preview /> : <RutaProtegida rolesPermitidos={['admin', 'estudiante']}><InnovationLayout /></RutaProtegida>}>
      <Route index element={<Navigate to="inicio" replace />} />
      {['inicio', 'certamen', 'hackatec', 'innobotica', 'innovaccion', 'retos', 'registros'].map(section => <Route key={section} path={section} element={<Innovation section={section} />} />)}
    </Route>)}
    <Route path="*" element={<div className="not-found"><h1>Página no encontrada</h1><p>La dirección no corresponde a una pantalla disponible.</p><Link className="button" to="/">Volver al inicio</Link></div>} />
  </Routes></Suspense></PageBoundary>;
}

export default function App() {
  return <BrowserRouter><PortalProvider><Seo /><AppRoutes /></PortalProvider></BrowserRouter>;
}
