import { hasStarted } from '../portal/schedule.js';
export const occupied = (data, event) => (event.ocupados || 0) + data.registrations.filter(r => r.event === event.id && r.estatus === 'Confirmada').length;
export const closed = event => event.estatus !== 'Activo' || hasStarted(event.fecha, event.hora);
