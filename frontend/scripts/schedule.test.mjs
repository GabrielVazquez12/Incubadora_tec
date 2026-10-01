import assert from 'node:assert/strict';
import { availableSlots, hasStarted, portalClock } from '../src/shared/portal/schedule.js';
const now = new Date('2026-10-02T00:30:00Z');
assert.deepEqual(portalClock(now), { date: '2026-10-01', time: '18:30' });
assert.equal(hasStarted('2026-10-01', '18:30', now), true);
assert.equal(hasStarted('2026-10-01', '18:31', now), false);
const slot = (id, inicio, fin, coordinador = 'admin') => ({ id, fecha: '2026-10-02', inicio, fin, coordinador });
const data = {
  users: [{ id: 'admin', rol: 'admin' }, { id: 'other', rol: 'admin' }, { id: 'former', rol: 'estudiante' }],
  slots: [slot('booked', '10:00', '11:00'), slot('overlap', '10:30', '11:30', 'other'),
    slot('adjacent', '11:00', '12:00'), slot('cancelled', '09:00', '10:00'),
    { ...slot('expired', '18:00', '19:00'), fecha: '2026-10-01' },
    slot('former', '13:00', '14:00', 'former'), { ...slot('reserved', '15:00', '16:00'), reservado: true }],
  appointments: [{ slot: 'booked', user: 'student', estatus: 'Confirmada' }, { slot: 'cancelled', user: 'student', estatus: 'Cancelada' }],
};
assert.deepEqual(availableSlots(data, 'student', now).map(s => s.id), ['cancelled', 'adjacent']);
assert.deepEqual(availableSlots(data, 'someone-else', now).map(s => s.id), ['cancelled', 'overlap', 'adjacent']);
console.log('PASS: timezone, expired slots, ownership overlap, cancellations, unavailable coordinators and ordering');
