import { useEffect, useId, useRef } from 'react';
import { usePortal } from './PortalContext.jsx';
import { passwordError } from '../registration/validation.js';

export function Heading({ eyebrow, title, description, action }) {
  return <header className="page-heading"><div><p className="eyebrow">{eyebrow || 'INCUBADORA ITS'}</p><h1>{title}</h1>{description && <p className="muted">{description}</p>}</div>{action}</header>;
}
export function Panel({ title, children, className = '' }) {
  return <section className={`panel ${className}`}>{title && <h2>{title}</h2>}{children}</section>;
}
export function Badge({ children }) {
  const positive = ['Activo', 'Completado', 'Pagado', 'Confirmada', 'Aprobada', 'Aprobado', 'Disponible'].includes(children);
  const negative = ['Rechazado', 'Rechazada', 'Cancelada', 'Cupo lleno', 'Correcciones solicitadas'].includes(children);
  return <span className={`badge ${positive ? 'positive' : negative ? 'negative' : 'pending'}`}>{children}</span>;
}
export function Progress({ value }) {
  return <div className="progress-wrap"><progress max="100" value={value} aria-label={`Progreso: ${value}%`} /><span>{value}%</span></div>;
}
export function Empty({ children = 'Todavía no hay registros para mostrar.' }) {
  return <div className="empty-state"><span aria-hidden="true">○</span><p>{children}</p></div>;
}
export function Table({ headings, children, empty = false }) {
  return empty ? <Empty /> : <div className="table-scroll"><table><thead><tr>{headings.map(h => <th key={h} scope="col">{h}</th>)}</tr></thead><tbody>{children}</tbody></table></div>;
}
export function Field({ label, children, ...props }) {
  const id = useId();
  if (!children && props.maxLength === undefined && (!props.type || ['text', 'search', 'email', 'password', 'tel'].includes(props.type))) props.maxLength = props.type === 'email' ? 254 : props.type === 'password' ? 72 : 160;
  return <label className="field" htmlFor={id}><span>{label}</span>{children ? <select id={id} {...props}>{children}</select> : <input id={id} {...props} />}</label>;
}
export function TextArea({ label, ...props }) {
  const id = useId();
  if (props.maxLength === undefined) props.maxLength = 3000;
  return <label className="field" htmlFor={id}><span>{label}</span><textarea id={id} rows="4" {...props} /></label>;
}
export function Modal({ title, children, onClose }) {
  const portal = usePortal();
  const ref = useRef(null);
  const id = useId();
  useEffect(() => { const dialog = ref.current; dialog.showModal(); return () => dialog.close(); }, []);
  return <dialog ref={ref} className="modal" aria-labelledby={id} onCancel={event => { if (portal?.busy) event.preventDefault(); else onClose(); }}><div className="modal-heading"><h2 id={id}>{title}</h2><button type="button" className="icon-button" disabled={portal?.busy} onClick={onClose} aria-label="Cerrar ventana">×</button></div>{portal?.error && <p className="error" role="alert">{portal.error}</p>}{children}</dialog>;
}
export function Stats({ items }) {
  return <div className="stats-grid">{items.map(([label, value, description]) => <section className="stat" key={label}><p>{label}</p><strong>{value}</strong>{description && <small>{description}</small>}</section>)}</div>;
}
export function download(name, content, type = 'text/plain;charset=utf-8') {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const a = document.createElement('a'); a.href = url; a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
export function exportCSV(name, headings, rows) {
  const cell = value => { let text = String(value ?? ''); if (/^[=+@\-\t\r]/.test(text)) text = `'${text}`; return `"${text.replaceAll('"', '""')}"`; };
  download(name, '\uFEFF' + [headings, ...rows].map(row => row.map(cell).join(',')).join('\r\n'), 'text/csv;charset=utf-8');
}
export const formValues = event => Object.fromEntries([...new FormData(event.currentTarget)].map(([key, value]) => [key, typeof value === 'string' && key !== 'password' ? value.trim() : value]));

export function Form({ onSubmit, children, busy = false, ...props }) {
  const portal = usePortal();
  const disabled = busy || portal?.busy;
  const inFlight = useRef(false);
  async function submit(event) {
    event.preventDefault();
    if (inFlight.current || disabled) return;
    for (const input of event.currentTarget.querySelectorAll('input:not(:disabled), textarea:not(:disabled)')) {
      if (!event.nativeEvent.submitter?.formNoValidate && input.required && !['file', 'checkbox', 'radio'].includes(input.type) && !input.value.trim()) {
        input.setCustomValidity('Completa este campo; no puede contener solamente espacios.');
        input.focus(); input.reportValidity(); return;
      }
      if (input.type === 'password' && input.value && passwordError(input.value, Math.max(1, input.minLength))) {
        input.setCustomValidity(passwordError(input.value, Math.max(1, input.minLength)));
        input.focus(); input.reportValidity(); return;
      }
    }
    inFlight.current = true;
    try { await onSubmit?.(event); } finally { inFlight.current = false; }
  }
  return <form {...props} onSubmit={submit} aria-busy={disabled || undefined} onInput={event => event.target.setCustomValidity?.('')}>
    <fieldset disabled={disabled} style={{ display: 'contents', border: 0, padding: 0, margin: 0 }}>{children}</fieldset>
  </form>;
}
