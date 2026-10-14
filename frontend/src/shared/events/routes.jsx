import { lazyPage } from '../portal/lazyPage.jsx';

const Events = lazyPage(() => import('./Events'), 'Events');
const Checkout = lazyPage(() => import('./Checkout'), 'Checkout');
const Registrations = lazyPage(() => import('./Registrations'), 'Registrations');

export const participantRoutes = [
  ['eventos', <Events />],
  ['eventos/:id/checkout', <Checkout />],
  ['inscripciones', <Registrations />],
];
