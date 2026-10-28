import { lazyPage } from '../../shared/portal/lazyPage.jsx';
import { participantRoutes } from '../../shared/events/routes';

const Application = lazyPage(() => import('../../shared/applications/Application'), 'Application');

export const externalRoutes = [
  ...participantRoutes,
  ['solicitud', <Application />],
];
