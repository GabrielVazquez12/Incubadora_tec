// Dates and times entered in the portal belong to the institution, not the device.
export function portalClock(now = new Date()) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Mexico_City', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(now).map(part => [part.type, part.value]));
  return { date: `${parts.year}-${parts.month}-${parts.day}`, time: `${parts.hour}:${parts.minute}` };
}

export function hasStarted(date, time, now = new Date()) {
  const clock = portalClock(now);
  return date < clock.date || (date === clock.date && time.slice(0, 5) <= clock.time);
}

export function availableSlots(data, userId, now = new Date()) {
  const own = data.appointments.filter(a => a.user === userId && a.estatus === 'Confirmada')
    .map(a => data.slots.find(s => s.id === a.slot)).filter(Boolean);
  return data.slots.filter(s => !hasStarted(s.fecha, s.inicio, now) && !s.reservado
    && data.users.some(u => u.id === s.coordinador && u.rol === 'admin')
    && !data.appointments.some(a => a.slot === s.id && a.estatus === 'Confirmada')
    && !own.some(other => other.fecha === s.fecha && other.inicio < s.fin && other.fin > s.inicio))
    .sort((a, b) => `${a.fecha}T${a.inicio}`.localeCompare(`${b.fecha}T${b.inicio}`));
}
