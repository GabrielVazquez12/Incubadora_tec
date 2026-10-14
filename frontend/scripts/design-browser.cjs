const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { randomUUID } = require('node:crypto');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL || 'http://127.0.0.1:8089');
  assert.ok(['localhost', '127.0.0.1'].includes(base.hostname), 'Use an isolated local test portal.');
  const artifacts = path.resolve(process.env.TEST_DESIGN_ARTIFACTS || path.resolve(__dirname, '../../.local/phase-a-screenshots'));
  await fs.mkdir(artifacts, { recursive: true });
  const page = await browser();
  assert.ok(page, 'Chrome is required.');
  const student = { nombre: 'Cuenta temporal de verificación', correo: `phase-a-${randomUUID()}@example.com`, password: randomUUID(), rol: 'estudiante' };
  async function checkLayout(expectedHeight) {
    await page.wait('document.fonts.status === "loaded"');
    const layout = await page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,overflow:Array.from(document.querySelectorAll("body *")).map(e=>({tag:e.tagName,classes:e.className?.baseVal||e.className,right:Math.round(e.getBoundingClientRect().right),width:Math.round(e.getBoundingClientRect().width)})).filter(e=>e.right>innerWidth+1).slice(0,8)})');
    if (layout.scroll > layout.width + 1) await page.screenshot(path.join(artifacts,'desbordamiento-diagnostico.png'));
    assert.ok(layout.scroll <= layout.width + 1, `No horizontal document overflow: ${JSON.stringify(layout)}`);
    assert.equal(await page.evaluate('document.querySelector(".identity-bar").getBoundingClientRect().height'), expectedHeight);
    await page.evaluate('window.scrollTo(0, 400)');
    assert.equal(await page.evaluate('Math.round(document.querySelector(".enlaces-header").getBoundingClientRect().top)'), 0, 'Header remains visible while scrolling');
    await page.evaluate('window.scrollTo(0,0)');
    await page.wait('Array.from(document.querySelectorAll(".brand-full img,.brand-symbol")).filter(i=>i.loading!=="lazy").every(i=>i.complete&&i.naturalWidth>0)');
  }
  async function login(account) {
    await page.navigate(new URL('/login', base).href);
    await page.fill('#correo', account.correo);
    await page.fill('#password', account.password);
    await page.evaluate('document.querySelector("form").requestSubmit()');
    try { await page.wait('!!document.querySelector(".portal-welcome")'); }
    catch (error) {
      console.error(JSON.stringify(await page.evaluate('({path:location.pathname,alert:document.querySelector("[role=alert]")?.textContent,hasEmail:!!document.querySelector("#correo")?.value,hasPassword:!!document.querySelector("#password")?.value})')));
      console.error(JSON.stringify(page.errors()));
      await page.screenshot(path.join(artifacts,'login-diagnostico.png'));
      throw error;
    }
    assert.ok(await page.evaluate('!document.querySelector("#contenido .module-grid") && !document.querySelector("#contenido a")'));
  }
  async function mobileMenu(expectedPaths) {
    await page.viewport(320, 900, 3);
    await checkLayout(56);
    await page.evaluate('document.querySelector(".identity-bar-inner > .menu-toggle").focus()');
    await page.press('Enter');
    try { await page.wait('document.querySelector(".mobile-menu").open'); }
    catch (error) {
      console.error(JSON.stringify(await page.evaluate('({active:document.activeElement.outerHTML.slice(0,400),expanded:document.querySelector(".identity-bar-inner > .menu-toggle").getAttribute("aria-expanded"),dialog:document.querySelector(".mobile-menu").open})')));
      console.error(JSON.stringify(page.errors()));
      await page.screenshot(path.join(artifacts,'menu-diagnostico.png'));
      throw error;
    }
    assert.ok(await page.evaluate('document.querySelector(".mobile-menu").contains(document.activeElement)'), 'Focus enters dialog');
    for (const target of expectedPaths) assert.ok(await page.evaluate(`!!document.querySelector('.mobile-menu a[href="${target}"]')`));
    const actor = await page.evaluate('location.pathname.split("/")[1] || "publico"');
    await page.screenshot(path.join(artifacts, `${actor}-menu-movil.png`));
    await page.press('Escape');
    await page.wait('!document.querySelector(".mobile-menu").open');
    assert.ok(await page.evaluate('document.activeElement === document.querySelector(".identity-bar-inner > .menu-toggle")'), 'Escape returns focus to menu trigger');
  }
  try {
    await page.viewport(1280, 900);
    await page.navigate(base.href);
    await checkLayout(72);
    assert.equal(await page.evaluate('document.querySelectorAll(".program-grid article").length'), 2);
    await page.screenshot(path.join(artifacts, 'inicio-escritorio.png'), true);
    await mobileMenu(['/','/incubadora','/innovatec','/vinculacion','/eventos','/contacto']);
    await page.screenshot(path.join(artifacts, 'inicio-movil.png'), true);
    await page.navigate(new URL('/login', base).href);
    await page.wait('document.querySelector(".brand-full img").complete');
    assert.ok(await page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), 'Login fits 320px');
    assert.ok(await page.evaluate('document.querySelector(".brand-full img").alt.includes("Enlaces Institucionales ITS")'));
    await page.screenshot(path.join(artifacts, 'acceso-movil.png'), true);
    await page.viewport(1280,900);
    await page.screenshot(path.join(artifacts, 'acceso-escritorio.png'), true);
    const response = await fetch(new URL('/api/auth/registro', base), { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(student) });
    assert.equal(response.status,201,'Create only an isolated synthetic student');
    await login(student);
    await checkLayout(72);
    await page.screenshot(path.join(artifacts, 'emprendedor-escritorio.png'), true);
    await mobileMenu(['inicio','boletin','proyectos','avances','eventos','tutorias','pagos','inscripciones'].map(item=>`/emprendedor/${item}`));
    try { await page.wait('document.querySelector(".brand-symbol").currentSrc.includes("monograma-144")'); }
    catch (error) {
      console.error(JSON.stringify(await page.evaluate('({dpr:devicePixelRatio,image:document.querySelector(".brand-symbol").outerHTML,current:document.querySelector(".brand-symbol").currentSrc})')));
      throw error;
    }
    await page.screenshot(path.join(artifacts, 'emprendedor-movil.png'), true);
    const coordinator = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN || path.resolve(__dirname,'../../.local/phase-a-admin.json'),'utf8'));
    await page.evaluate('localStorage.clear()');
    await page.viewport(1280,900);
    await login(coordinator);
    await checkLayout(72);
    await page.evaluate(`document.querySelector('button[aria-label="Mostrar opciones de Reportes"]').focus()`);
    await page.press('ArrowDown');
    await page.wait('!!document.querySelector(".navigation-dropdown") && !document.querySelector(".navigation-dropdown").hidden');
    assert.ok(await page.evaluate('document.querySelector(".navigation-dropdown").contains(document.activeElement)'));
    await page.screenshot(path.join(artifacts, 'coordinador-submenu-escritorio.png'));
    await page.press('Escape');
    await page.wait('!document.querySelector(".navigation-dropdown") || document.querySelector(".navigation-dropdown").hidden');
    assert.equal(await page.evaluate('document.activeElement.getAttribute("aria-label")'), 'Mostrar opciones de Reportes');
    await page.screenshot(path.join(artifacts, 'coordinador-escritorio.png'), true);
    await mobileMenu(['inicio','boletin','usuarios','roles','eventos','publicaciones','pagos','reportes','tutorias','seguimiento','solicitudes','registros'].map(item=>`/coordinador/${item}`));
    await page.screenshot(path.join(artifacts, 'coordinador-movil.png'), true);
    assert.equal(page.errors().length,0,'No browser runtime exceptions');
    console.log('PASS: official brand, desktop/mobile headers, 320px without overflow, sticky header, role navigation, 14 destinations, keyboard submenus, Escape/focus, 3x images and unchanged real login.');
  } finally { await page.close(); }
}
main().catch(error=>{console.error(error.message);process.exitCode=1;});
