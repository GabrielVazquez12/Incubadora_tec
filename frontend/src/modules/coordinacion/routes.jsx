import { lazyPage } from '../../shared/portal/lazyPage.jsx';

const EventManagement = lazyPage(() => import('./EventManagement'), 'EventManagement');
const EventForm = lazyPage(() => import('./EventManagement'), 'EventForm');
const Publications = lazyPage(() => import('./Publications.jsx'), 'default');
const Users = lazyPage(() => import('./Users'), 'Users');
const Roles = lazyPage(() => import('./Users'), 'Roles');
const Reports = lazyPage(() => import('./Reports'), 'Reports');
const RegistrationReview = lazyPage(() => import('./RegistrationReview'), 'default');
const Projects = lazyPage(() => import('../../shared/projects/Projects'), 'Projects');
const ProjectDetail = lazyPage(() => import('../../shared/projects/Projects'), 'ProjectDetail');
const Application = lazyPage(() => import('../../shared/applications/Application'), 'Application');
const Tutoring = lazyPage(() => import('../../shared/tutoring/Tutoring'), 'Tutoring');

export const coordinationRoutes = [
  ['publicaciones', <Publications />],
  ['eventos', <EventManagement />],
  ['usuarios', <Users />],
  ['roles', <Roles />],
  ['eventos/nuevo', <EventForm />],
  ['eventos/:id/editar', <EventForm />],
  ['eventos/inscripciones', <EventManagement initialTab="inscripciones" />],
  ['eventos/tipos', <EventManagement initialTab="tipos" />],
  ['inscripciones', <EventManagement initialTab="inscripciones" />],
  ['seguimiento', <Projects />],
  ['seguimiento/:id', <ProjectDetail />],
  ['reportes', <Reports />],
  ...['proyectos', 'emprendedores', 'avances', 'estadisticas'].map(tab => [`reportes/${tab}`, <Reports initialTab={tab} />]),
  ['solicitudes', <Application admin />],
  ['registros', <RegistrationReview />],
  ['tutorias', <Tutoring />],
  ...['agenda', 'historial', 'disponibilidad'].map(tab => [`tutorias/${tab}`, <Tutoring initialTab={tab} />]),
];
