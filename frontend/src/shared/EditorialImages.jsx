import { useEffect, useState } from 'react';
import api from './api/client.js';
import { errorMessage } from './portal/PortalContext.jsx';
import { Modal } from './portal/ui.jsx';
import './editorial-images.css';

function Picture({ image, authenticated = false, expanded = false }) {
  const [url, setUrl] = useState('');
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    if (!authenticated) return;
    const controller = new AbortController();
    let objectUrl;
    setUrl(''); setFailed(false);
    api.get(`/portal/media/${image.id}`, { responseType: 'blob', signal: controller.signal }).then(response => {
      if (controller.signal.aborted) return;
      objectUrl = URL.createObjectURL(response.data); setUrl(objectUrl);
    }).catch(() => { if (!controller.signal.aborted) setFailed(true); });
    return () => { controller.abort(); if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [image.id, authenticated]);
  const src = authenticated ? url : `${api.defaults.baseURL.replace(/\/$/, '')}${image.url}`;
  if (failed) return <span role="status">No se pudo cargar la imagen.</span>;
  return src ? <><img src={src} alt={image.alt} loading="lazy" decoding="async" onError={() => setFailed(true)} />{expanded && <a className="text-link" href={src} target="_blank" rel="noreferrer">Abrir imagen en tamaño completo ↗</a>}</> : <span role="status">Cargando imagen…</span>;
}

export function ImageGallery({ images = [], authenticated = false }) {
  const [selected, setSelected] = useState(null);
  if (!images.length) return null;
  return <><div className="editorial-gallery">{images.map(image => <button className="editorial-picture" type="button" key={image.id} onClick={() => setSelected(image)} aria-label={`Ampliar imagen: ${image.alt}`}><Picture image={image} authenticated={authenticated} /><span>Ver imagen completa ↗</span></button>)}</div>{selected && <Modal title={selected.alt} onClose={() => setSelected(null)}><div className="editorial-viewer"><Picture image={selected} authenticated={authenticated} expanded /></div></Modal>}</>;
}

export function ImageEditor({ kind, itemId, onChanged }) {
  const [images, setImages] = useState([]);
  const [file, setFile] = useState(null);
  const [alt, setAlt] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const [inputKey, setInputKey] = useState(0);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    setImages([]); setFile(null); setAlt(''); setError(''); setInputKey(n => n + 1);
    if (!itemId) return;
    const controller = new AbortController();
    setLoading(true);
    api.get(`/admin/media/${kind}/${itemId}`, { signal: controller.signal }).then(response => setImages(response.data)).catch(e => { if (!controller.signal.aborted) setError(errorMessage(e)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [kind, itemId, attempt]);
  async function upload() {
    if (!file || !alt.trim()) { setError('Selecciona una imagen y escribe una descripción breve.'); return; }
    if (file.size > 8 * 1024 * 1024) { setError('La imagen debe pesar como máximo 8 MB.'); return; }
    setBusy(true); setError('');
    try {
      const form = new FormData(); form.append('file', file); form.append('alt', alt.trim());
      const response = await api.post(`/admin/media/${kind}/${itemId}`, form);
      setImages(previous => [...previous, response.data]); setFile(null); setAlt(''); setInputKey(n => n + 1); await onChanged?.();
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function remove(image) {
    setBusy(true); setError('');
    try { await api.delete(`/admin/media/${image.id}`); setImages(previous => previous.filter(item => item.id !== image.id)); await onChanged?.(); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  return <section className="editorial-editor" aria-label="Imágenes y flyers"><h3>Imágenes y flyers</h3><p className="helper">Hasta cinco imágenes JPG, PNG o WebP de 8 MB cada una. Los flyers se muestran completos, sin recortar.</p>{!itemId ? <p className="helper">Guarda primero la publicación o el evento para adjuntar sus imágenes.</p> : <>
    {loading && <p role="status">Cargando galería…</p>}
    <ImageGallery images={images} authenticated />
    <div className="editorial-remove">{images.map((image, i) => <button type="button" key={image.id} className="text-button danger" disabled={busy} onClick={() => remove(image)}>Retirar imagen {i + 1}: {image.alt}</button>)}</div>
    <fieldset disabled={busy || loading || images.length >= 5}><label className="field"><span>Selecciona una imagen o flyer</span><input key={inputKey} type="file" accept="image/jpeg,image/png,image/webp" onChange={e => setFile(e.target.files?.[0] || null)} /></label><label className="field"><span>Descripción de la imagen (accesibilidad)</span><input maxLength={300} value={alt} onChange={e => setAlt(e.target.value)} placeholder="Ej. Flyer del taller de emprendimiento con fecha y sede" /></label><button type="button" className="button secondary" onClick={upload}>{busy ? 'Guardando…' : 'Agregar imagen'}</button></fieldset>
    {images.length >= 5 && <p className="helper">Galería completa. Retira una imagen para agregar otra.</p>}{error && <p className="error" role="alert">{error} <button type="button" className="text-button" disabled={busy} onClick={() => setAttempt(n => n + 1)}>Actualizar galería</button></p>}
  </>}</section>;
}
