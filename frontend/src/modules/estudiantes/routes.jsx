import { lazyPage } from '../../shared/portal/lazyPage.jsx';
import { participantRoutes } from '../../shared/events/routes';

const ProjectForm = lazyPage(() => import('./ProjectForm'), 'ProjectForm');
const Projects = lazyPage(() => import('../../shared/projects/Projects'), 'Projects');
const ProjectDetail = lazyPage(() => import('../../shared/projects/Projects'), 'ProjectDetail');
const Tutoring = lazyPage(() => import('../../shared/tutoring/Tutoring'), 'Tutoring');

export const studentRoutes = [
  ...participantRoutes,
  ['proyectos', <Projects />],
  ['proyectos/nuevo', <ProjectForm />],
  ['proyectos/:id', <ProjectDetail />],
  ['proyectos/:id/editar', <ProjectForm />],
  ['avances', <ProjectDetail advances />],
  ['tutorias', <Tutoring />],
  ...['agenda', 'historial', 'agendar'].map(tab => [`tutorias/${tab}`, <Tutoring initialTab={tab} />]),
];
