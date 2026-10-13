// Native Chrome DevTools smoke test; only runs against a local isolated portal.
const assert = require('node:assert/strict');
const { randomUUID } = require('node:crypto');
const { browser } = require('./browser-helper.cjs');

async function main() {
  const base = new URL(process.env.TEST_PORTAL_URL || 'http://127.0.0.1:8089');
  assert.ok(['localhost', '127.0.0.1'].includes(base.hostname), 'Use a local isolated test portal.');
  const page = await browser();
  assert.ok(page, 'Chrome is required for the browser smoke test.');
  const email = `browser-${randomUUID()}@example.com`;
  const password = randomUUID();
  async function set(selector, value) {
    await page.fill(selector, value);
  }
  async function submitTwice(selector = 'form') {
    await page.evaluate(`(() => { const form = document.querySelector(${JSON.stringify(selector)}); form.requestSubmit(); form.requestSubmit(); })()`);
  }
  try {
    await page.navigate(new URL('/registro', base).href);
    await page.wait(`!!document.querySelector('#nombre')`);
    await page.evaluate(`(() => {
      window.__requests = [];
      const open = XMLHttpRequest.prototype.open, send = XMLHttpRequest.prototype.send;
      XMLHttpRequest.prototype.open = function(method, url, ...args) { this.__method = method; this.__url = String(url); return open.call(this, method, url, ...args); };
      XMLHttpRequest.prototype.send = function(body) {
        window.__requests.push(this.__method + ' ' + this.__url);
        const rejectLogin = window.__failLogin && this.__url.endsWith('/auth/login');
        const rejectSave = window.__failSave && this.__method === 'PUT';
        const rejectRefresh = window.__failRefresh && this.__url.endsWith('/portal/state');
        if (rejectLogin || rejectSave || rejectRefresh) {
          window.__failLogin = window.__failSave = window.__failRefresh = false;
          setTimeout(() => this.dispatchEvent(new ProgressEvent('error')), 0); return;
        }
        return send.call(this, body);
      };
    })()`);
    await set('#nombre', '   '); await set('#correo', email); await set('#password', password);
    await submitTwice();
    assert.equal(await page.evaluate('window.__requests.length'), 0, 'Whitespace name must be rejected before sending.');
    await set('#nombre', "María O'Neill-Güemes"); await set('#password', 'á'.repeat(37));
    await submitTwice();
    assert.equal(await page.evaluate('window.__requests.length'), 0, 'Passwords over 72 UTF-8 bytes must be rejected.');
    await set('#password', password); await submitTwice();
    await page.wait(`location.pathname === '/login'`);
    assert.equal(await page.evaluate(`window.__requests.filter(r => r.includes('/auth/registro')).length`), 1, 'Double submission must create one account.');
    await set('#correo', email); await set('#password', password);
    await page.evaluate('window.__failLogin = true'); await submitTwice();
    await page.wait(`!!document.querySelector('[role="alert"]') && !document.querySelector('fieldset').disabled`);
    assert.equal(await page.evaluate(`document.querySelector('#correo').value`), email, 'Recoverable failure must preserve the email.');
    assert.ok(await page.evaluate(`document.querySelector('[role="alert"]').textContent.includes('conectar')`), 'Network errors must be distinguishable from bad credentials.');
    await submitTwice();
    await page.wait(`location.pathname === '/emprendedor/inicio' && document.body.textContent.includes('María')`);
    // SPA navigation preserves the request observer.
    await page.evaluate(`document.querySelector('a[href="/emprendedor/proyectos"]').click()`);
    await page.wait(`!!document.querySelector('a[href="/emprendedor/proyectos/nuevo"]')`);
    await page.evaluate(`document.querySelector('a[href="/emprendedor/proyectos/nuevo"]').click()`);
    await page.wait(`!!document.querySelector('[name="empresa.nombre"]')`);
    await set('[name="empresa.nombre"]', 'Proyecto de navegador');
    await page.evaluate(`(() => { window.__failSave = true; const form = document.querySelector('form'); form.requestSubmit(form.querySelector('[value="Borrador"]')); })()`);
    await page.wait(`document.body.textContent.includes('No se pudo conectar') && !document.querySelector('fieldset').disabled`);
    assert.equal(await page.evaluate(`document.querySelector('[name="empresa.nombre"]').value`), 'Proyecto de navegador');
    await page.evaluate(`(() => { window.__failRefresh = true; const form = document.querySelector('form'); const button = form.querySelector('[value="Borrador"]'); form.requestSubmit(button); form.requestSubmit(button); })()`);
    await page.wait(`document.body.textContent.includes('Borrador guardado') && document.body.textContent.includes('La operación se guardó')`);
    const rows = await page.evaluate(`fetch('/api/portal/state', {headers: {Authorization: 'Bearer ' + localStorage.getItem('access_token')}}).then(r => r.json()).then(r => r.data.initialRegistrations)`);
    assert.equal(rows.length, 1, 'The confirmed draft must not be duplicated after a refresh failure.');
    assert.equal(rows[0].datos['empresa.nombre'], 'Proyecto de navegador');
    assert.equal(rows[0].estatus, 'Borrador', 'Partial drafts must remain available.');
    assert.deepEqual(page.errors(), [], 'Browser must not report runtime exceptions.');
    console.log('PASS: real Chrome registration, UTF-8 limits, double submission, login recovery and partial draft preservation.');
  } finally { await page.close(); }
}
main().catch(error => { console.error(error.message); process.exitCode = 1; });
