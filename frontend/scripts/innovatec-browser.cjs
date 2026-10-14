const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL || 'http://127.0.0.1:8091');
  assert.ok(['127.0.0.1', 'localhost'].includes(base.hostname), 'Only an isolated local portal is allowed.');
  const admin = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const artifacts = path.resolve(process.env.TEST_DESIGN_ARTIFACTS);
  const account = { nombre: 'Emprendedor temporal de prueba', correo: `qa-innova-${randomUUID()}@example.com`, password: randomUUID(), rol: 'estudiante' };
  const response = await fetch(new URL('/api/auth/registro', base), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(account) });
  assert.equal(response.status, 201);
  const page = await browser();
  assert.ok(page, 'Chrome is required.');
  async function login(person) {
    await page.navigate(new URL('/login', base).href);
    await page.fill('#correo', person.correo); await page.fill('#password', person.password);
    await page.evaluate('document.querySelector("form").requestSubmit()');
    await page.wait('!!document.querySelector(".portal-welcome")');
  }
  async function layout() {
    const dimensions = await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})');
    if (dimensions.scroll > dimensions.width + 1) {
      console.error(await page.evaluate('Array.from(document.querySelectorAll("body *")).map(e=>({tag:e.tagName,classes:typeof e.className==="string"?e.className:"",name:e.getAttribute("name"),right:Math.round(e.getBoundingClientRect().right),width:Math.round(e.getBoundingClientRect().width)})).filter(e=>e.right>innerWidth+1).slice(0,20)'));
      await page.screenshot(path.join(artifacts, 'innova-desbordamiento-diagnostico.png'), true);
    }
    assert.ok(dimensions.scroll <= dimensions.width + 1, `No horizontal overflow: ${JSON.stringify(dimensions)}`);
  }
  try {
    await page.viewport(1280, 900);
    await login(admin);
    await page.navigate(new URL('/coordinador/innovatec/convocatoria', base).href);
    await page.wait('!!document.querySelector("input[name=titulo]")');
    await page.fill('input[name=titulo]', 'Convocatoria temporal de verificación');
    await page.fill('textarea[name=descripcion]', 'Convocatoria sintética exclusiva de la base temporal.');
    for (const [name, date] of [['apertura', new Date(Date.now() - 86400000)], ['cierre', new Date(Date.now() + 7 * 86400000)]]) {
      await page.evaluate(`(() => { const input=document.querySelector('input[name="${name}"]'); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(input,${JSON.stringify(date.toISOString().slice(0,10))}); input.dispatchEvent(new Event('input',{bubbles:true})); input.dispatchEvent(new Event('change',{bubbles:true})); })()`);
    }
    await page.fill('textarea[name=requisitos]', 'Ficha temporal');
    await page.fill('textarea[name=aviso_privacidad]', 'Aviso sintético de prueba; no es un aviso institucional aprobado para uso real.');
    await page.evaluate('document.querySelector("input[name=aviso_aprobado]").click();document.querySelector("input[name=publicada]").click();document.querySelector("input[name=titulo]").form.requestSubmit()');
    await page.wait('!!document.querySelector(".notice") && document.querySelector(".notice").textContent.includes("guardados")');
    await page.viewport(320, 900, 3); await layout();
    await page.screenshot(path.join(artifacts, 'innova-convocatoria-movil.png'), true);
    await page.navigate(new URL('/innovatec/convocatoria', base).href);
    await page.wait('document.body.textContent.includes("Convocatoria temporal de verificación")');
    await layout();
    await page.evaluate('localStorage.clear()');
    await login(account);
    await page.navigate(new URL('/innovatec/inscripcion', base).href);
    try { await page.wait('!!document.querySelector("input[name=nombre]")'); }
    catch (error) {
      console.error(await page.evaluate('({path:location.pathname,heading:document.querySelector("h1")?.textContent,text:document.body.textContent.slice(0,2400)})'));
      console.error(page.errors());
      await page.screenshot(path.join(artifacts, 'innova-captura-diagnostico.png'), true);
      throw error;
    }
    await page.fill('input[name=nombre]', 'Proyecto temporal con innovación');
    await page.fill('input[name=equipo]', 'Equipo temporal de prueba');
    await page.fill('textarea[name=descripcion]', 'Datos sintéticos para validar la captura real en Chrome.');
    await page.fill('input[name=integrante_0_nombre]', account.nombre);
    await page.fill('input[name=integrante_0_correo]', account.correo);
    await page.fill('input[name=integrante_0_carrera]', 'Carrera temporal');
    await page.fill('input[name=integrante_0_semestre]', '4');
    await page.fill('input[name=integrante_1_nombre]', 'Asesora temporal de prueba');
    await page.fill('input[name=integrante_1_correo]', `advisor-${randomUUID()}@example.com`);
    await layout();
    await page.screenshot(path.join(artifacts, 'innova-inscripcion-movil.png'), true);
    await page.evaluate('document.querySelector("input[name=privacidad]").click()');
    const invalid = await page.evaluate('Array.from(document.querySelector("input[name=nombre]").form.elements).filter(e=>e.willValidate&&!e.checkValidity()).map(e=>({name:e.name,type:e.type,message:e.validationMessage}))');
    assert.deepEqual(invalid, [], 'All captured inputs pass native browser validation before submission');
    await page.evaluate('document.querySelector("input[name=nombre]").form.requestSubmit();document.querySelector("input[name=nombre]").form.requestSubmit()');
    try { await page.wait('document.body.textContent.includes("Inscripción confirmada")'); }
    catch (error) { console.error(await page.evaluate('Array.from(document.querySelectorAll("[role=alert]")).map(e=>e.textContent)')); throw error; }
    const route = await page.evaluate('Array.from(document.querySelectorAll("a")).find(a=>a.textContent.includes("Abrir expediente")).href');
    await page.navigate(route);
    await page.wait('document.body.textContent.includes("Folio: ITS-INN")');
    await layout();
    await page.screenshot(path.join(artifacts, 'innova-equipo-movil.png'), true);
    const result = await page.evaluate('fetch("/api/portal/innovatec/equipos",{headers:{Authorization:"Bearer "+localStorage.getItem("access_token")}}).then(r=>r.json()).then(data=>({total:data.total,id:data.items[0].id}))');
    assert.equal(result.total, 1, 'Double submission does not create another team');
    await page.viewport(1280, 900); await layout();
    await page.screenshot(path.join(artifacts, 'innova-equipo-escritorio.png'), true);
    await page.evaluate('localStorage.clear()'); await login(admin);
    await page.navigate(new URL(`/coordinador/innovatec/equipos/${result.id}`, base).href);
    await page.wait('Array.from(document.forms).some(f=>f.getAttribute("aria-label")==="Revisión de propuesta InnovaTec")');
    await page.evaluate('Array.from(document.forms).find(f=>f.getAttribute("aria-label")==="Revisión de propuesta InnovaTec").requestSubmit()');
    await page.wait('document.body.textContent.includes("Revisión guardada")');
    await page.wait('document.body.textContent.includes("Folio: ITS-INN")');
    await page.viewport(320, 900, 3); await layout();
    await page.screenshot(path.join(artifacts, 'innova-coordinacion-movil.png'), true);
    assert.equal(page.errors().length, 0, 'No browser runtime exceptions');
    console.log('PASS: real Chrome convocatoria, consent, structured roster, confirmation, double submission, owner/admin team detail, existing proposal review and mobile/desktop layout.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
