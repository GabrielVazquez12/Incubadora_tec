const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL);
  assert.ok(['127.0.0.1', 'localhost'].includes(base.hostname), 'Only an isolated local portal is allowed.');
  const admin = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const artifacts = path.resolve(process.env.TEST_DESIGN_ARTIFACTS);
  const page = await browser(); assert.ok(page);
  async function login() {
    await page.navigate(new URL('/login', base).href);
    await page.fill('#correo', admin.correo); await page.fill('#password', admin.password);
    await page.evaluate('document.querySelector("form").requestSubmit()');
    await page.wait('!!document.querySelector(".portal-welcome")');
  }
  async function select(selector, value) {
    await page.evaluate(`(() => { const input=document.querySelector(${JSON.stringify(selector)}); input.value=${JSON.stringify(value)};input.dispatchEvent(new Event('change',{bubbles:true})); })()`);
  }
  async function layout(name) {
    const dimensions = await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');
    assert.ok(dimensions.scroll <= dimensions.width + 1, `${name}: ${JSON.stringify(dimensions)}`);
    await page.screenshot(path.join(artifacts, name), true);
  }
  try {
    await page.viewport(1280, 900); await login();
    await page.navigate(new URL('/coordinador/encuestas', base).href);
    await page.wait('!!document.querySelector("input[name=titulo]")');
    await page.fill('input[name=titulo]', 'Encuesta temporal de navegador');
    await page.fill('textarea[name=descripcion]', 'Encuesta sintética exclusiva de la base local.');
    for (const [name, delta] of [['apertura', -2], ['cierre', 7]]) {
      const date = new Date(Date.now() + delta * 86400000).toISOString().slice(0, 10);
      await page.evaluate(`(() => { const input=document.querySelector('input[name="${name}"]');Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(date)}); input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true})); })()`);
    }
    const kinds = ['seleccion_unica', 'multiseleccion', 'escala', 'texto'];
    for (let index = 0; index < kinds.length; index++) {
      if (index) await page.evaluate('Array.from(document.querySelectorAll("button")).find(button=>button.textContent==="Agregar pregunta").click()');
      await page.wait(`!!document.querySelector('input[name="pregunta_${index}"]')`);
      await page.fill(`input[name=pregunta_${index}]`, ['Participación', 'Necesidades', 'Valoración', 'Comentario'][index]);
      await select(`select[name=tipo_${index}]`, kinds[index]);
      if (index < 2) await page.fill(`textarea[name=opciones_${index}]`, index ? 'Mercado\nVentas' : 'Sí\nNo');
    }
    await page.evaluate('document.querySelector("input[name=publicada]").click();document.querySelector("input[name=titulo]").form.requestSubmit()');
    await page.wait('document.body.textContent.includes("Encuesta guardada.")');
    const survey = await page.evaluate('fetch("/api/portal/encuestas",{headers:{Authorization:"Bearer "+localStorage.getItem("access_token")}}).then(r=>r.json()).then(rows=>rows.find(row=>row.titulo==="Encuesta temporal de navegador"))');
    assert.ok(survey.id);
    await page.viewport(320, 900, 3); await layout('encuestas-constructor-movil.png');
    await page.evaluate('localStorage.clear()');
    await page.navigate(new URL(`/encuestas/${survey.id}`, base).href);
    await page.wait('!!document.querySelector("input[type=radio]")');
    await page.evaluate('document.querySelector("input[type=radio]").click();document.querySelector("input[type=checkbox]").click()');
    await select(`select[name="${survey.preguntas[2].id}"]`, '3');
    await page.fill('textarea', 'Información clara con café y piñón; datos sintéticos.');
    await layout('encuestas-respuesta-movil.png');
    await page.evaluate('document.querySelector("form").requestSubmit();document.querySelector("form").requestSubmit()');
    await page.wait('document.body.textContent.includes("Tu respuesta quedó registrada.")');
    await page.navigate(new URL(`/encuestas/${survey.id}`, base).href);
    await page.wait('document.body.textContent.includes("Tu respuesta quedó registrada.")');
    assert.equal(await page.evaluate('document.querySelectorAll("form").length'), 0, 'Cookie preserves answered state');
    await page.viewport(1280, 900); await login();
    await page.navigate(new URL('/coordinador/encuestas/resultados', base).href);
    await page.wait('Array.from(document.querySelectorAll("tr")).some(row=>row.textContent.includes("Encuesta temporal de navegador"))');
    await page.evaluate('Array.from(document.querySelectorAll("tr")).find(row=>row.textContent.includes("Encuesta temporal de navegador")).querySelectorAll("button")[1].click()');
    await page.wait('document.body.textContent.includes("1 respuestas reales")');
    await layout('encuestas-resultados-escritorio.png');
    await page.viewport(320, 900, 3); await layout('encuestas-resultados-movil.png');
    assert.equal(page.errors().length, 0);
    console.log('PASS: real Chrome survey builder, four question types, anonymous cookie, duplicate submission, persisted confirmation and protected charts/results at 320px and desktop.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
