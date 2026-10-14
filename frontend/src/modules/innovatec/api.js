import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../../shared/api/client.js';
import { errorMessage } from '../../shared/portal/PortalContext.jsx';

export const states = { inscrito: 'Inscrito', documentacion_recibida: 'Documentación recibida', etapa_local: 'Etapa local', acreditado: 'Acreditado', etapa_regional: 'Etapa regional', etapa_nacional: 'Etapa nacional', no_acreditado: 'No acreditado', baja: 'Baja' };

export function useRemote(path, enabled = true) {
  const [data, setData] = useState(null), [error, setError] = useState(''), [loading, setLoading] = useState(enabled);
  const [revision, setRevision] = useState(0);
  const reload = useCallback(() => setRevision(n => n + 1), []);
  useEffect(() => {
    if (!enabled) { setLoading(false); return; }
    const controller = new AbortController();
    setLoading(true); setError('');
    api.get(path, { signal: controller.signal }).then(r => { if (!controller.signal.aborted) setData(r.data); }).catch(e => { if (!controller.signal.aborted) setError(errorMessage(e)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [path, enabled, revision]);
  return { data, setData, loading, error, reload };
}

export function useAction() {
  const [busy, setBusy] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const inFlight = useRef(false);
  async function run(action, message = 'Cambios guardados.') {
    if (inFlight.current) return null;
    inFlight.current = true; setBusy(true); setError(''); setNotice('');
    try { const result = await action(); setNotice(message); return result; }
    catch (e) { setError(errorMessage(e)); return null; }
    finally { inFlight.current = false; setBusy(false); }
  }
  return { run, busy, error, notice, setError };
}

export async function downloadAsset(path, name) {
  let response;
  try { response = await api.get(path, { responseType: 'blob' }); }
  catch (error) {
    if (error.response?.data instanceof Blob) {
      try { error.response.data = JSON.parse(await error.response.data.text()); } catch { /* Preserve the original HTTP error. */ }
    }
    throw error;
  }
  const url = URL.createObjectURL(response.data), link = document.createElement('a');
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  return true;
}

export function uploadBody(event, extra = {}) {
  const body = new FormData(event.currentTarget), file = body.get('file');
  if (!(file instanceof File) || !file.size || file.size > 5 * 1024 * 1024) {
    const error = new Error(); error.response = { data: { detail: 'Adjunta un PDF, DOC o DOCX no vacío de hasta 5 MB.' } }; throw error;
  }
  Object.entries(extra).forEach(([key, value]) => body.set(key, value));
  return body;
}
