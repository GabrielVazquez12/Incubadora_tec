const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL);
  assert.ok(['127.0.0.1', 'localhost'].includes(base.hostname), 'Only an isolated local portal is allowed.');
  const admin = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const artifacts = path.resolve(process.env.TEST_DESIGN_ARTIFACTS);
  const page = await browser(); assert.ok(page, 'Chrome is required.');
  async function navigate(route, ready) {
    await page.navigate(new URL(route, base).href);
    await page.wait(ready);
    assert.deepEqual(page.errors(), []);
  }
  async function login() {
    await navigate('/login', '!!document.querySelector("#correo")');
    await page.fill('#correo', admin.correo); await page.fill('#password', admin.password);
    await page.evaluate('document.querySelector("form").requestSubmit()');
    await page.wait('!!document.querySelector(".portal-welcome")');
  }
  async function select(name, value) {
    await page.evaluate(`(() => { const input=document.querySelector('select[name="${name}"]'); input.value=${JSON.stringify(value)};input.dispatchEvent(new Event('change',{bubbles:true})); })()`);
  }
  async function api(method, route, payload) {
    return page.evaluate(`fetch('/api${route}', {method:${JSON.stringify(method)},headers:{'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('access_token')},${payload === undefined ? '' : `body:JSON.stringify(${JSON.stringify(payload)}),`}}).then(async r=>{if(!r.ok)throw new Error(r.status+': '+await r.text());return r.json()})`);
  }
  async function layout(name) {
    await page.wait('document.fonts.status === "loaded"');
    const dimensions = await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');
    assert.ok(dimensions.scroll <= dimensions.width + 1, `${name}: ${JSON.stringify(dimensions)}`);
    await page.screenshot(path.join(artifacts, name), true);
    assert.deepEqual(page.errors(), []);
  }
  async function submitContaining(name) {
    await page.evaluate(`document.querySelector('[name="${name}"]').form.requestSubmit()`);
    await page.wait('!!document.querySelector(".notice")');
    assert.equal(await page.evaluate('Array.from(document.querySelectorAll(".error")).map(e=>e.textContent).join(" ")'), '');
  }
  try {
    await page.viewport(1280, 900); await login();
    const state = await api('GET', '/portal/state');
    const owner = state.user.id;
    await navigate('/coordinador/difusion', '!!document.querySelector("input[name=titulo]")');
    await page.fill('input[name=titulo]', 'Pieza temporal de navegador');
    await select('responsable_id', owner);
    await page.fill('input[name=enlace]', 'https://example.com/actividad');
    await select('estado', 'publicada');
    await page.evaluate('document.querySelector("input[name=visible]").click()');
    await submitContaining('titulo');
    await page.wait('Array.from(document.querySelectorAll("tr")).some(row=>row.textContent.includes("Pieza temporal de navegador"))');
    await layout('difusion-calendario-escritorio.png');
    await page.evaluate('Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Nuevo registro").click()');
    await page.wait('document.querySelector("input[name=titulo]").value === ""');
    await page.viewport(320, 900, 3); await layout('difusion-calendario-movil.png');
    await navigate('/coordinador/difusion/visitas', '!!document.querySelector("input[name=grupo]")');
    await page.fill('input[name=grupo]', 'Grupo temporal');
    await page.fill('input[name=docente_coordinador]', 'Docente temporal');
    await select('responsable_id', owner);
    await page.fill('input[name=asistentes]', '24');
    await page.fill('textarea[name=resultado]', 'Orientación sintética registrada.');
    await submitContaining('grupo');
    await layout('difusion-visitas-movil.png');
    await navigate('/coordinador/difusion/plantillas', '!!document.querySelector("input[name=titulo]")');
    await page.fill('input[name=titulo]', 'Plantilla temporal de navegador');
    await page.fill('textarea[name=contenido]', 'Mensaje sintético para orientación.');
    await submitContaining('titulo');
    await page.wait('document.querySelector("select[name=plantilla_id]").options.length > 1');
    const template = await page.evaluate('document.querySelector("select[name=plantilla_id]").options[1].value');
    await select('plantilla_id', template); await select('responsable_id', owner);
    await page.fill('input[name=destinatario]', 'Grupo sintético sin envío real');
    await submitContaining('destinatario');
    await page.wait('document.body.textContent.includes("Envío realizado registrado")');
    await layout('difusion-plantillas-envios-movil.png');
    await navigate('/coordinador/difusion/preguntas', '!!document.querySelector("input[name=pregunta]")');
    await page.fill('input[name=pregunta]', '¿Cómo iniciar mi proyecto de prueba?');
    await page.fill('textarea[name=respuesta]', 'Consulta el diagnóstico y registra tu proyecto.');
    await submitContaining('pregunta');
    await layout('difusion-faq-movil.png');
    const config = await api('GET', '/portal/incubadora/configuracion');
    await api('PUT', '/portal/incubadora/configuracion', {version:config.version,aviso_privacidad:'Aviso sintético aprobado solo para prueba local.',aviso_aprobado:true});
    await navigate('/coordinador/difusion/contacto', '!!document.querySelector("textarea[name=vinculacion]")');
    await page.fill('textarea[name=vinculacion]', 'Vinculación institucional sintética de prueba.');
    await page.fill('input[name=correo]', 'orientacion@example.com');
    await page.fill('input[name=telefono]', '8441234567');
    await page.fill('input[name=horario]', 'Horario sintético de prueba');
    await page.fill('input[name=instagram]', 'https://example.com/institucion');
    await submitContaining('vinculacion');
    await page.viewport(1280, 900); await layout('difusion-configuracion-escritorio.png');
    await navigate('/coordinador/eventos/fichas', '!!document.querySelector("input[name=titulo]")');
    await page.evaluate('Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Cargar eventos proporcionados").click()');
    await page.wait('document.querySelectorAll("tbody tr").length === 3');
    await page.evaluate('document.querySelector("tbody tr button").click()');
    await page.evaluate('document.querySelector("input[name=publicada]").click()');
    await submitContaining('titulo');
    const announcement = (await api('GET', '/portal/difusion/fichas')).items.find(item => item.publicada);
    assert.ok(announcement);
    await layout('difusion-fichas-escritorio.png');
    await page.evaluate('localStorage.clear()');
    await navigate('/difusion', 'document.body.textContent.includes("Pieza temporal de navegador")');
    await layout('difusion-publica-escritorio.png');
    await page.viewport(320, 900, 3); await layout('difusion-publica-movil.png');
    await navigate('/incubadora', 'document.body.textContent.includes("¿Cómo iniciar mi proyecto de prueba?")');
    await navigate('/vinculacion', 'document.body.textContent.includes("Vinculación institucional sintética de prueba.")');
    assert.ok(await page.evaluate('document.querySelector("footer").textContent.includes("orientacion@example.com")'));
    assert.equal(await page.evaluate(`document.querySelector('footer a[href="https://example.com/institucion"]').textContent`), 'Instagram');
    await layout('difusion-vinculacion-movil.png');
    await navigate('/contacto', '!!document.querySelector("input[name=nombre]")');
    await page.fill('input[name=nombre]', 'Contacto sintético de Chrome');
    await page.fill('input[name=correo]', 'contact-browser@example.com');
    await page.fill('input[name=asunto]', 'Orientación de prueba');
    await page.fill('textarea[name=mensaje]', 'Consulta sintética para el portal.');
    await page.evaluate('document.querySelector("input[name=acepto_privacidad]").click()');
    await page.evaluate('document.querySelector("input[name=nombre]").form.requestSubmit();document.querySelector("input[name=nombre]").form.requestSubmit()');
    await page.wait('document.body.textContent.includes("Mensaje recibido. Folio:")');
    await layout('difusion-contacto-confirmado-movil.png');
    await navigate('/eventos', '!!document.querySelector(".outreach-workspace .panel")');
    await page.wait(`!!document.querySelector('a[href="/eventos/${announcement.id}"]')`);
    await page.evaluate(`document.querySelector('a[href="/eventos/${announcement.id}"]').click()`);
    try { await page.wait('document.body.textContent.includes("No hay inscripciones abiertas para esta ficha.")'); }
    catch (error) { console.error(JSON.stringify(page.errors())); throw error; }
    await layout('difusion-evento-movil.png');
    await navigate('/aviso-de-privacidad', 'document.body.textContent.includes("Aviso sintético aprobado solo para prueba local.")');
    await login();
    await navigate('/coordinador/difusion/contacto', 'Array.from(document.querySelectorAll("tr")).some(r=>r.textContent.includes("Contacto sintético de Chrome"))');
    await page.evaluate('Array.from(document.querySelectorAll("tr")).find(r=>r.textContent.includes("Contacto sintético de Chrome")).querySelector("button").click()');
    await select('estado', 'atendido'); await page.fill('textarea[name=nota]', 'Atención sintética en Chrome.');
    await submitContaining('nota');
    await page.wait('document.body.textContent.includes("Estado de atención registrado")');
    await layout('difusion-contacto-bandeja-movil.png');
    console.log('PASS: Chrome outreach CRUD, new-record reset, templates/manual sends, FAQ, configured footer, public events, consent/contact double-submit and private review at desktop and 320px.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
