const fs = require("node:fs/promises");
const path = require("node:path");
const { spawn } = require("node:child_process");
async function browser() {
  const executable = process.env.TEST_CHROME || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  try { await fs.access(executable); } catch { return null; }
  const root = path.resolve(__dirname, "..");
  const directory = await fs.mkdtemp(path.join(root, ".test-browser-"));
  const child = spawn(executable, ["--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check", "--remote-debugging-port=0", `--user-data-dir=${directory}`, "about:blank"], { windowsHide: true, stdio: "ignore" });
  let port;
  for (let attempt = 0; attempt < 600; attempt++) {
    try { port = (await fs.readFile(path.join(directory, "DevToolsActivePort"), "utf8")).split("\n")[0]; break; }
    catch { await new Promise(resolve => setTimeout(resolve, 100)); }
  }
  if (!port) { child.kill(); throw new Error("No se pudo iniciar Chrome para verificar formularios."); }
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const tab = targets.find(target => target.type === "page");
  const socket = new WebSocket(tab.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.addEventListener("open", resolve, { once: true }); socket.addEventListener("error", reject, { once: true }); });
  let sequence = 0;
  let runtimeErrors = [];
  const waiting = new Map();
  socket.addEventListener("close", () => {
    for (const pending of waiting.values()) pending.reject(new Error("La sesión de pruebas del navegador se cerró."));
    waiting.clear();
  });
  socket.addEventListener("message", event => {
    const data = JSON.parse(event.data);
    if (data.method === "Runtime.exceptionThrown") runtimeErrors.push(data.params.exceptionDetails.exception?.description || data.params.exceptionDetails.text);
    if (data.method === "Page.javascriptDialogOpening") {
      call("Page.handleJavaScriptDialog", { accept: true }).catch(() => {});
      return;
    }
    const pending = waiting.get(data.id);
    if (!pending) return;
    waiting.delete(data.id);
    data.error ? pending.reject(new Error(data.error.message)) : pending.resolve(data.result);
  });
  function call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++sequence;
      waiting.set(id, { resolve, reject });
      socket.send(JSON.stringify({ id, method, params }));
    });
  }
  async function evaluate(expression) {
    const result = await call("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
    if (result.exceptionDetails) throw new Error(result.exceptionDetails.exception?.description || result.exceptionDetails.text);
    return result.result.value;
  }
  await call("Page.enable");
  await call("Runtime.enable");
  async function wait(expression) {
    for (let attempt = 0; attempt < 100; attempt++) {
      try { if (await evaluate(expression)) return; } catch { /* page may be navigating */ }
      await new Promise(resolve => setTimeout(resolve, 100));
    }
    throw new Error(`La pantalla no completó la acción: ${expression}`);
  }
  return {
    evaluate, wait,
    async viewport(width, height, deviceScaleFactor = 1) {
      await call('Emulation.setDeviceMetricsOverride', { width, height, deviceScaleFactor, mobile: false });
    },
    async press(key, modifiers = 0) {
      const codes = { Tab: 9, Enter: 13, Escape: 27, ArrowDown: 40, ArrowUp: 38 };
      if (!codes[key]) throw new Error('Tecla no admitida por las pruebas de navegación.');
      const event = { key, code: key, windowsVirtualKeyCode: codes[key], nativeVirtualKeyCode: codes[key], modifiers };
      await call('Input.dispatchKeyEvent', { ...event, type: 'keyDown', ...(key === 'Enter' ? { text: '\r', unmodifiedText: '\r' } : {}) });
      await call('Input.dispatchKeyEvent', { ...event, type: 'keyUp' });
    },
    async screenshot(destination, fullPage = false) {
      let clip;
      if (fullPage) {
        await evaluate('window.scrollTo(0, document.documentElement.scrollHeight)');
        await wait('Array.from(document.images).every(image => image.complete && image.naturalWidth > 0)');
        await evaluate('window.scrollTo(0,0)');
        const metrics = await call('Page.getLayoutMetrics');
        clip = { ...metrics.cssContentSize, scale: 1 };
      }
      const shot = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: fullPage, ...(clip ? { clip } : {}) });
      await fs.writeFile(destination, Buffer.from(shot.data, 'base64'));
    },
    async fill(selector, value) {
      await evaluate(`(() => { const input = document.querySelector(${JSON.stringify(selector)}); input.focus(); input.select(); })()`);
      // Email inputs do not consistently support the selection API. Use the
      // native select-all shortcut, as a user would, before replacing text.
      const selectAll = { key: 'a', code: 'KeyA', windowsVirtualKeyCode: 65, nativeVirtualKeyCode: 65, modifiers: 2 };
      await call('Input.dispatchKeyEvent', { ...selectAll, type: 'keyDown' });
      await call('Input.dispatchKeyEvent', { ...selectAll, type: 'keyUp' });
      await call("Input.insertText", { text: value });
    },
    errors: () => runtimeErrors,
    async navigate(url) {
      runtimeErrors = [];
      const navigation = await call("Page.navigate", { url });
      if (navigation.errorText) throw new Error(navigation.errorText);
      if (navigation.loaderId) {
        for (let attempt = 0; attempt < 100; attempt++) {
          const tree = await call('Page.getFrameTree');
          if (tree.frameTree.frame.loaderId === navigation.loaderId) break;
          await new Promise(resolve => setTimeout(resolve, 100));
        }
      }
      await wait(`location.href === ${JSON.stringify(url)} && document.readyState === 'complete'`);
    },
    async close() {
      const done = child.exitCode !== null ? Promise.resolve() : new Promise(resolve => child.once("exit", resolve));
      await call("Browser.close").catch(() => {});
      socket.close();
      const timeout = setTimeout(() => { if (child.exitCode === null) child.kill(); }, 10000);
      await done; clearTimeout(timeout);
      if (path.resolve(directory).startsWith(path.join(root, ".test-browser-"))) await fs.rm(directory, { recursive: true, force: true, maxRetries: 15, retryDelay: 500 });
    }
  };
}
module.exports = { browser };
