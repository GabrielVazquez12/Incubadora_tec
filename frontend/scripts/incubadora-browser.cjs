const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL);
  assert.ok(['127.0.0.1', 'localhost'].includes(base.hostname), 'Only isolated local data is allowed.');
  const admin = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const account = { nombre: 'Titular de diagnóstico temporal', correo: `qa-incubadora-${randomUUID()}@example.com`, password: randomUUID(), rol: 'estudiante' };
  async function request(method, route, body, token) {
    const multipart = body instanceof FormData;
    const response = await fetch(new URL(`/api${route}`, base), { method, headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(body && !multipart ? { 'Content-Type': 'application/json' } : {}) }, ...(body ? { body: multipart ? body : JSON.stringify(body) } : {}) });
    const result = await response.json();
    assert.ok(response.ok, `${method} ${route}: ${response.status} ${JSON.stringify(result)}`);
    return result;
  }
  await request('POST', '/auth/registro', account);
  const token = (await request('POST', '/auth/login', { correo: account.correo, password: account.password })).access_token;
  const coordinator = (await request('POST', '/auth/login', { correo: admin.correo, password: admin.password })).access_token;
  const call = (await request('GET', '/public/innovatec/convocatorias'))[0];
  assert.ok(call, 'Run InnovaTec browser preparation before Incubadora.');
  let team = await request('POST', '/portal/innovatec/equipos', { id: randomUUID(), convocatoria_id: call.id, nombre: 'Proyecto temporal canalizado a diagnóstico', equipo: 'Equipo temporal de continuidad', descripcion: 'Continuidad de prueba entre ambos módulos.', categoria: call.categorias[0], integrantes: [{ nombre: account.nombre, correo: account.correo, carrera: 'Carrera temporal', semestre: 4, tipo: 'participante' }, { nombre: 'Asesor temporal', correo: `asesor-${randomUUID()}@example.com`, carrera: '', semestre: null, tipo: 'asesor' }], acepto_privacidad: true, version_convocatoria: call.version }, token);
  for (const requirement of call.requisitos) {
    const body = new FormData(); body.set('requisito', requirement); body.set('file', new Blob(['%PDF-1.4\nDocumento sintético\n%%EOF'], { type: 'application/pdf' }), 'ficha-temporal.pdf');
    team = await request('POST', `/portal/innovatec/equipos/${team.id}/documentos`, body, token);
    const document = team.documentos.find(item => item.requisito === requirement && item.vigente);
    team = await request('POST', `/portal/innovatec/documentos/${document.id}/revision`, { estado: 'aprobado', estado_anterior: 'recibido', comentarios: 'Verificado exclusivamente en la prueba local.' }, coordinator);
  }
  await request('PUT', `/portal/innovation/${team.innovacion_id}`, { ...team.propuesta, estatus: 'Aprobada', estatus_anterior: 'En revisión', equipo_version: team.version, comentario: 'Propuesta temporal aprobada para probar continuidad.' }, coordinator);
  team = await request('GET', `/portal/innovatec/equipos/${team.id}`, null, coordinator);
  for (const state of ['documentacion_recibida', 'etapa_local', 'acreditado']) team = await request('POST', `/portal/innovatec/equipos/${team.id}/estado`, { estado: state, version: team.version, motivo: 'Transición sintética de verificación' }, coordinator);
  const referral = await request('POST', `/portal/innovatec/equipos/${team.id}/canalizar`, {}, coordinator);
  const config = await request('GET', '/portal/incubadora/configuracion', null, coordinator);
  await request('PUT', '/portal/incubadora/configuracion', { version: config.version, dias_inactividad: 15, aviso_privacidad: 'Aviso sintético exclusivo de esta base temporal; sin validez institucional.', aviso_aprobado: true }, coordinator);
  await request('POST', '/portal/incubadora/catalogo/propuesta', {}, coordinator);
  const page = await browser(); assert.ok(page);
  const artifacts = path.resolve(process.env.TEST_DESIGN_ARTIFACTS);
  async function login(person) {
    await page.navigate(new URL('/login', base).href);
    await page.fill('#correo', person.correo); await page.fill('#password', person.password);
    await page.evaluate('document.querySelector("form").requestSubmit()');
    await page.wait('!!document.querySelector(".portal-welcome")');
  }
  async function layout(name) {
    const dimensions = await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');
    assert.ok(dimensions.scroll <= dimensions.width + 1, `${name}: horizontal overflow ${JSON.stringify(dimensions)}`);
    await page.screenshot(path.join(artifacts, name), true);
  }
  try {
    await page.viewport(1280, 900); await login(account);
    await page.navigate(new URL(`/emprendedor/proyectos/${referral.proyecto_id}`, base).href);
    await page.wait('document.body.textContent.includes("Expediente institucional")');
    await page.evaluate('Array.from(document.querySelectorAll("button")).find(button=>button.textContent.includes("Capturar o actualizar diagnóstico")).click()');
    await page.wait('!!document.querySelector("input[name=telefono]")');
    await page.fill('input[name=telefono]', '8441234567');
    await page.fill('input[name=carrera]', 'Carrera temporal'); await page.fill('input[name=semestre]', '4');
    await page.fill('textarea[name=descripcion]', 'Diagnóstico temporal: validar mercado y costos.');
    await page.evaluate('document.querySelector("input[name=necesidades]").click();document.querySelector("input[name=acepto_privacidad]").click();document.querySelector("input[name=telefono]").form.requestSubmit()');
    await page.wait('document.body.textContent.includes("Frecuencia: cada 15 días")');
    await page.viewport(320, 900, 3); await layout('incubadora-expediente-movil.png');
    await page.viewport(1280, 900); await layout('incubadora-expediente-escritorio.png');
    await page.navigate(new URL('/incubadora/registro', base).href);
    await page.wait('!!document.querySelector("input[name=nombre]")');
    await page.fill('input[name=nombre]', 'Captura pública temporal');
    await page.fill('textarea[name=producto_servicio]', 'Servicio temporal de verificación');
    await page.fill('input[name=telefono]', '8441234567');
    await page.fill('input[name=carrera]', 'Carrera temporal'); await page.fill('input[name=semestre]', '4');
    await page.fill('textarea[name=descripcion]', 'Diagnóstico público simplificado sin formato heredado.');
    await page.evaluate('document.querySelector("input[name=necesidades]").click();document.querySelector("input[name=acepto_privacidad]").click();document.querySelector("input[name=telefono]").form.requestSubmit();document.querySelector("input[name=telefono]").form.requestSubmit()');
    await page.wait('document.body.textContent.includes("Registro confirmado")');
    await page.viewport(320, 900, 3); await layout('incubadora-registro-publico-movil.png');
    const registered = await request('GET', '/portal/state', null, token);
    assert.equal(registered.data.projects.length, 2, 'Public duplicate submit creates only one additional project');
    await page.evaluate('localStorage.clear()'); await login(admin);
    await page.navigate(new URL(`/coordinador/seguimiento/${referral.proyecto_id}`, base).href);
    await page.wait('!!document.querySelector("textarea[name=actividad]")');
    await page.fill('textarea[name=actividad]', 'Entrevistar a tres posibles clientes y entregar notas.');
    await page.evaluate(`document.querySelector('select[name=responsable_id]').value=${JSON.stringify((await request('GET', `/portal/incubadora/proyectos/${referral.proyecto_id}`, null, token)).titular.id)};document.querySelector('textarea[name=actividad]').form.requestSubmit()`);
    await page.wait('document.body.textContent.includes("Cambios guardados.")');
    await page.viewport(320, 900, 3); await layout('incubadora-atencion-movil.png');
    const dossier = await request('GET', `/portal/incubadora/proyectos/${referral.proyecto_id}`, null, coordinator);
    assert.equal(dossier.atenciones.length, 1); assert.ok(dossier.atenciones[0].fecha_revision);
    await page.navigate(new URL('/coordinador/reportes/indicadores', base).href);
    await page.wait('document.body.textContent.includes("Actividades completadas")'); await layout('incubadora-indicadores-movil.png');
    assert.equal(page.errors().length, 0);
    console.log('PASS: real Chrome InnovaTec-to-Incubadora continuity, owner diagnostic and consent, coordinator agreement/review, real indicators, mobile/desktop and existing project route.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
