const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL);
  assert.ok(['localhost', '127.0.0.1'].includes(base.hostname));
  const admin = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const fixture = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_GOVERNANCE, 'utf8'));
  const artifacts = process.env.TEST_DESIGN_ARTIFACTS;
  for (const [route, status] of [['/incubadora', 200], ['/innovatec', 200], ['/incubadora/proyectos', 200], ['/innovatec/equipos', 200], ['/robots.txt', 200], ['/sitemap.xml', 200], ['/not-a-real-page', 404], ['/403', 403]]) {
    const response = await fetch(new URL(route, base));
    assert.equal(response.status, status, route);
    const content = await response.text();
    if (route === '/incubadora') { assert.ok(content.includes('<title>Incubadora de Empresas')); assert.ok(content.includes('rel="canonical"')); }
    if (route === '/sitemap.xml') { assert.ok(content.includes('/incubadora')); assert.ok(!content.includes('/coordinador')); }
  }
  const privatePage = await fetch(new URL('/coordinador/usuarios', base));
  assert.equal(privatePage.headers.get('x-robots-tag'), 'noindex, nofollow');
  assert.equal(privatePage.headers.get('x-frame-options'), 'DENY');
  const page = await browser(); assert.ok(page);
  async function navigate(route, condition) { await page.navigate(new URL(route, base).href); await page.wait(condition); assert.deepEqual(page.errors(), []); }
  async function login(account) {
    await page.navigate(new URL('/login', base).href);
    await page.fill('#correo', account.correo); await page.fill('#password', account.password);
    await page.evaluate('document.querySelector("form").requestSubmit()'); await page.wait('!!document.querySelector(".portal-welcome")');
  }
  async function select(selector, value) { await page.evaluate(`(() => {const e=document.querySelector(${JSON.stringify(selector)});e.value=${JSON.stringify(value)};e.dispatchEvent(new Event('change',{bubbles:true}));})()`); }
  async function configure(email, value) {
    await navigate('/coordinador/roles/accesos', 'document.querySelectorAll("tbody tr").length > 0');
    await page.evaluate(`Array.from(document.querySelectorAll('tbody tr')).find(r=>r.textContent.includes(${JSON.stringify(email)})).querySelector('button').click()`);
    await select('select[name=perfil]', value); await page.fill('textarea[name=motivo]', 'Cambio sintético de verificación.');
    await page.evaluate('document.querySelector("textarea[name=motivo]").form.requestSubmit()');
  }
  async function layout(name) {
    await page.wait('document.fonts.status === "loaded"');
    assert.ok(await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'));
    await page.screenshot(path.join(artifacts, name), true); assert.deepEqual(page.errors(), []);
  }
  try {
    await page.viewport(1280, 900); await login(admin);
    await configure(admin.correo, 'administrador'); await page.wait('location.pathname === "/login"'); await login(admin);
    await configure(fixture.advisor.correo, 'asesor'); await page.wait('!!document.querySelector(".notice")');
    await layout('f-perfiles-escritorio.png');
    await navigate('/coordinador/usuarios', 'document.querySelectorAll("tbody tr").length > 0');
    await page.evaluate(`Array.from(document.querySelectorAll('tbody tr')).find(row=>row.textContent.includes(${JSON.stringify(fixture.advisor.correo)})).querySelector('button').click()`);
    await select('dialog select[name=rol]', 'admin');
    await page.evaluate('document.querySelector("dialog select[name=rol]").form.requestSubmit()');
    await page.wait('document.querySelector("dialog[open] [role=alert]")?.textContent.includes("Revoca primero el perfil Asesor")');
    await layout('f-cambio-rol-protegido.png');
    await navigate(`/coordinador/seguimiento/${fixture.project}`, '!!document.querySelector("select[name=asesor_id]")');
    await select('select[name=asesor_id]', fixture.advisor.id);
    await page.evaluate('document.querySelector("select[name=asesor_id]").form.requestSubmit()');
    await page.wait('!!document.querySelector(".notice")');
    await page.evaluate('localStorage.clear()'); await login(fixture.advisor);
    const advisorToken = await page.evaluate('localStorage.getItem("access_token")');
    await navigate('/emprendedor/asesoria', 'document.body.textContent.includes("Expediente sintético asignado")');
    assert.ok(!(await page.evaluate('document.body.textContent')).includes('Expediente sintético ajeno'));
    await page.evaluate('Array.from(document.querySelectorAll("a")).find(a=>a.textContent==="Abrir expediente").click()');
    await page.wait('!!document.querySelector("textarea[name=actividad]")');
    await page.fill('textarea[name=actividad]', 'Asesoría sintética de navegador.');
    await page.fill('textarea[name=siguiente_accion]', 'Validar la propuesta sintética.');
    const review = new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10);
    await page.evaluate(`(() => { const input = document.querySelector('input[name=fecha_revision]'); input.value = ${JSON.stringify(review)}; input.dispatchEvent(new Event('input', {bubbles:true})); input.dispatchEvent(new Event('change', {bubbles:true})); })()`);
    await page.evaluate('document.querySelector("textarea[name=actividad]").form.requestSubmit()');
    try { await page.wait('document.body.textContent.includes("Atención registrada.")'); }
    catch (error) {
      console.error(JSON.stringify(await page.evaluate('({alerts:Array.from(document.querySelectorAll("[role=alert]")).map(e=>e.textContent),invalid:Array.from(document.querySelectorAll(":invalid")).map(e=>({name:e.name,value:e.value,reason:e.validationMessage})),fields:Array.from(document.querySelectorAll("form input,form select,form textarea")).map(e=>({name:e.name,value:e.value}))})')));
      console.error(JSON.stringify(page.errors())); await page.screenshot(path.join(artifacts, 'f-atencion-diagnostico.png')); throw error;
    }
    await layout('f-asesor-expediente-escritorio.png');
    await page.viewport(320, 900, 3); await layout('f-asesor-expediente-movil.png');
    await navigate(`/emprendedor/asesoria/${fixture.foreign}`, '!!document.querySelector(".error")');
    assert.ok(!(await page.evaluate('document.body.textContent')).includes('Expediente sintético ajeno'));
    await page.evaluate('localStorage.clear()'); await login(admin);
    await navigate('/coordinador/roles/auditoria', 'document.querySelectorAll("tbody tr").length > 0');
    await layout('f-auditoria-movil.png');
    await configure(fixture.advisor.correo, 'sin_perfil'); await page.wait('!!document.querySelector(".notice")');
    assert.equal((await fetch(new URL('/api/portal/gobierno/expedientes', base), {headers:{Authorization:`Bearer ${advisorToken}`}})).status, 401);
    await page.evaluate('localStorage.clear()'); await login(fixture.advisor);
    await navigate('/emprendedor/asesoria', 'document.body.textContent.includes("Acceso restringido")');
    await layout('f-revocacion-403-movil.png');
    console.log('PASS: server SEO/robots/sitemap/403/404, administrator bootstrap, advisor assignment/isolation/attention, audit UI and immediate token revocation in Chrome at desktop and 320px.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
