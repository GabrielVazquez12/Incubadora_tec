const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL);
  assert.ok(['localhost', '127.0.0.1'].includes(base.hostname));
  const account = JSON.parse(await fs.readFile(process.env.TEST_DESIGN_ADMIN, 'utf8'));
  const login = await fetch(new URL('/api/auth/login', base), {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({correo:account.correo,password:account.password})});
  assert.equal(login.status, 200);
  const token = (await login.json()).access_token;
  const title = 'Noticia sintética de carga diferida';
  const created = await fetch(new URL('/api/admin/publications', base), {method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${token}`},body:JSON.stringify({titulo:title,resumen:'Información sintética de verificación.',contenido:'Contenido sintético para verificar el enlace directo.',categoria:'Noticia',fecha:new Date(Date.now()-86400000).toISOString().slice(0,10),publicada:true})});
  assert.equal(created.status, 201);
  const publication = await created.json();
  const page = await browser(); assert.ok(page);
  try {
    await page.viewport(390, 844, 2);
    await page.navigate(base.href);
    assert.equal(await page.evaluate('document.querySelectorAll(".news-card").length'), 0, 'Below-fold articles are not mounted during the initial hero render');
    await page.evaluate('document.querySelector("#actualidad").scrollIntoView()');
    await page.wait(`document.querySelector('#actualidad').textContent.includes(${JSON.stringify(title)})`);
    assert.deepEqual(page.errors(), []);
    await page.screenshot(path.join(process.env.TEST_DESIGN_ARTIFACTS, 'f-boletin-diferido-movil.png'), true);
    await page.navigate(new URL(`/?noticia=${publication.id}`, base).href);
    await page.wait(`document.querySelector('dialog.modal[open]')?.textContent.includes(${JSON.stringify(title)})`);
    assert.deepEqual(page.errors(), []);
    await page.screenshot(path.join(process.env.TEST_DESIGN_ARTIFACTS, 'f-noticia-enlace-directo.png'));
    // Block only this document's future module loads, then verify the visible retry recovers on reload.
    await page.navigate(base.href);
    await page.evaluate(`(() => { const policy=document.createElement('meta'); policy.httpEquiv='Content-Security-Policy'; policy.content="script-src 'none'"; document.head.append(policy); document.querySelector('a[href="/login"]').click(); })()`);
    await page.wait('document.body.textContent.includes("No se pudo cargar esta pantalla")');
    await page.screenshot(path.join(process.env.TEST_DESIGN_ARTIFACTS, 'f-recuperacion-carga.png'));
    await page.evaluate('Array.from(document.querySelectorAll("button")).find(button=>button.textContent==="Reintentar").click()');
    await page.wait('!!document.querySelector("#correo")');
    console.log('PASS: deferred below-fold newsletter loads on approach, direct news link opens without scrolling, and failed route chunk displays a retry that recovers on reload.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
