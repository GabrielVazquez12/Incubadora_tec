import { useState } from 'react';
import { usePortal } from '../portal/PortalContext.jsx';
import { usePortalRoute } from '../portal/PortalLayout.jsx';
import { Badge, Field, Modal, Panel, Table, TextArea, formValues } from '../portal/ui.jsx';
import { dateLabel } from '../portal/data.js';

export function Documents({ project }) {
  const { data, busy, preview, uploadDocument, reviewDocument, downloadFile, notify } = usePortal();
  const { role } = usePortalRoute();
  const [modal, setModal] = useState(null);
  const [error, setError] = useState('');
  const rows = (data.documents || []).filter(d => d.proyecto_id === project.id);
  function open(kind, document = null) { setError(''); setModal({ kind, document }); }
  async function upload(event) {
    event.preventDefault();
    const file = new FormData(event.currentTarget).get('file');
    if (!file?.size || file.size > 5 * 1024 * 1024 || !/\.(pdf|docx?)$/i.test(file.name)) {
      setError('Selecciona un PDF, DOC o DOCX de hasta 5 MB.'); return;
    }
    setError('');
    if (await uploadDocument(project.id, file, modal.document?.id)) {
      setModal(null); notify('Documento enviado a revisión.');
    }
  }
  async function review(event) {
    event.preventDefault();
    const { estatus, observaciones } = formValues(event);
    if (estatus === 'Correcciones solicitadas' && !observaciones.trim()) {
      setError('Indica qué debe corregir el emprendedor.'); return;
    }
    setError('');
    if (await reviewDocument(modal.document.id, estatus, modal.document.estatus, observaciones)) {
      setModal(null); notify('Revisión del documento guardada.');
    }
  }
  return <Panel title="Documentos del proyecto">
    <p>Adjunta documentos PDF o Word de hasta 5 MB. Las correcciones conservan las versiones anteriores.</p>
    <button type="button" className="button small" disabled={busy || preview} onClick={() => open('upload')}>Subir documento</button>
    {preview && <p className="helper">Inicia sesión para cargar y revisar documentos.</p>}
    <Table headings={['Documento', 'Estado', 'Observaciones', 'Acciones']} empty={!rows.length}>
      {rows.map(doc => <tr key={doc.id}>
        <td><strong>{doc.nombre}</strong><small>{dateLabel(doc.creado_en)}{!doc.vigente && ' · Versión anterior'}</small>
          {doc.reemplaza_id && <small>Corrige: {rows.find(d => d.id === doc.reemplaza_id)?.nombre || 'documento anterior'}</small>}</td>
        <td><Badge>{doc.estatus}</Badge></td><td>{doc.observaciones || 'Sin observaciones'}</td>
        <td><div className="row">
          <button type="button" className="text-button" disabled={!doc.available} onClick={() => downloadFile({ id: doc.id, name: doc.nombre })}>Descargar</button>
          {role === 'admin' && doc.vigente && <button type="button" className="text-button" disabled={busy} onClick={() => open('review', doc)}>Revisar</button>}
          {doc.vigente && doc.estatus === 'Correcciones solicitadas' && <button type="button" className="text-button" disabled={busy} onClick={() => open('upload', doc)}>Enviar corrección</button>}
          <button type="button" className="text-button" onClick={() => open('history', doc)}>Historial</button>
        </div></td>
      </tr>)}
    </Table>
    {modal && <Modal title={modal.kind === 'upload' ? modal.document ? 'Enviar corrección' : 'Subir documento' : modal.kind === 'review' ? 'Revisar documento' : 'Historial del documento'} onClose={() => !busy && setModal(null)}>
      {modal.document && <p><strong>{modal.document.nombre}</strong></p>}
      {error && <p role="alert" className="error">{error}</p>}
      {modal.kind === 'upload' && <form className="form-stack" onSubmit={upload}>
        {modal.document?.observaciones && <p className="info-box">{modal.document.observaciones}</p>}
        <Field label="Archivo PDF o Word (máximo 5 MB)" name="file" type="file" accept=".pdf,.doc,.docx" required disabled={busy} />
        <button className="button" disabled={busy}>{busy ? 'Enviando…' : 'Enviar a revisión'}</button>
      </form>}
      {modal.kind === 'review' && <form className="form-stack" onSubmit={review}>
        <Field label="Resultado" name="estatus" defaultValue={modal.document.estatus === 'Aprobado' ? 'Correcciones solicitadas' : 'Aprobado'} disabled={busy}>
          <option>Aprobado</option><option>Correcciones solicitadas</option>
        </Field>
        <TextArea label="Observaciones (obligatorias al solicitar correcciones)" name="observaciones" maxLength={2000} disabled={busy} />
        <button className="button" disabled={busy}>Guardar revisión</button>
      </form>}
      {modal.kind === 'history' && <Table headings={['Fecha', 'Estado', 'Responsable', 'Observaciones']} empty={!modal.document.historial?.length}>
        {(modal.document.historial || []).map((h, i) => <tr key={i}><td>{dateLabel(h.fecha)}</td><td>{h.estatus}</td><td>{h.nombre}</td><td>{h.observaciones}</td></tr>)}
      </Table>}
    </Modal>}
  </Panel>;
}
