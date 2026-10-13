import { useEffect, useId, useRef, useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import InstitutionalBrand from '../InstitutionalBrand.jsx';
import Icon from './Icon.jsx';

export default function Navigation({ home, items, account, publicSite = false }) {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(null);
  const dialog = useRef(null);
  const trigger = useRef(null);
  const dropdown = useRef(null);
  const dropdownTrigger = useRef(null);
  const header = useRef(null);
  const id = useId();
  const location = useLocation();

  useEffect(() => { setOpen(false); setExpanded(null); }, [location.pathname, location.search]);
  useEffect(() => {
    if (open && !dialog.current.open) dialog.current.showModal();
    if (!open && dialog.current.open) { dialog.current.close(); trigger.current?.focus(); }
  }, [open]);
  useEffect(() => {
    if (!expanded) return;
    dropdown.current?.querySelector('a')?.focus();
    const close = event => {
      if (event.type === 'keydown' && event.key !== 'Escape') return;
      if (event.type === 'pointerdown' && header.current?.contains(event.target)) return;
      setExpanded(null);
      if (event.type === 'keydown') dropdownTrigger.current?.focus();
    };
    document.addEventListener('keydown', close);
    document.addEventListener('pointerdown', close);
    window.addEventListener('resize', close);
    return () => { document.removeEventListener('keydown', close); document.removeEventListener('pointerdown', close); window.removeEventListener('resize', close); };
  }, [expanded]);

  function toggle(event, item) {
    if (expanded?.label === item.label) { setExpanded(null); return; }
    dropdownTrigger.current = event.currentTarget;
    const rect = event.currentTarget.getBoundingClientRect();
    setExpanded({ ...item, left: Math.max(8, Math.min(rect.left, window.innerWidth - 288)), top: rect.bottom + 8 });
  }
  const link = (item, mobile = false) => <NavLink key={item.to} to={item.to} end={item.end} className={item.accent ? 'innovation-link' : undefined} onClick={() => { if (mobile) setOpen(false); setExpanded(null); }}>{item.label}{item.accent && <Icon name="external" />}{item.description && <span className="sr-only">{item.description}</span>}</NavLink>;

  return <header ref={header} className={`enlaces-header ${publicSite ? 'public-header' : ''}`}>
    <div className="identity-bar"><div className="identity-bar-inner"><NavLink className="brand-home" to={home} aria-label="Enlaces Institucionales ITS, inicio"><InstitutionalBrand /></NavLink><div className="desktop-account">{account}</div><button ref={trigger} className="menu-toggle" type="button" aria-expanded={open} aria-controls={id} aria-haspopup="dialog" onClick={() => setOpen(true)}><Icon name="menu" /><span className="sr-only">Abrir menú principal</span></button></div></div>
    <nav className="desktop-navigation" aria-label="Navegación principal"><div className="navigation-scroll" onScroll={() => setExpanded(null)}>{items.map(item => <div className={`navigation-item ${item.accent ? 'navigation-last' : ''}`} key={item.to}>{link(item)}{item.children?.length > 0 && <button type="button" className="submenu-toggle" aria-label={`Mostrar opciones de ${item.label}`} aria-expanded={expanded?.label === item.label} aria-controls={`${id}-submenu`} onClick={event => toggle(event, item)} onKeyDown={event => { if (event.key === 'ArrowDown') { event.preventDefault(); toggle(event, item); } }}><Icon name="chevron" /></button>}</div>)}</div></nav>
    {expanded && <nav ref={dropdown} id={`${id}-submenu`} className="navigation-dropdown" style={{ left: expanded.left, top: expanded.top }} aria-label={`Opciones de ${expanded.label}`}>{expanded.children.map(item => link(item))}</nav>}
    <dialog ref={dialog} id={id} className="mobile-menu" aria-labelledby={`${id}-title`} onCancel={event => { event.preventDefault(); setOpen(false); }} onClose={() => setOpen(false)}>
      <div className="mobile-menu-heading"><h2 id={`${id}-title`}>Menú principal</h2><button type="button" className="menu-toggle" onClick={() => setOpen(false)} aria-label="Cerrar menú principal"><Icon name="close" /></button></div>
      <div className="mobile-account">{account}</div>
      <nav aria-label="Navegación principal móvil">{items.map(item => <div className="mobile-navigation-item" key={item.to}>{link(item, true)}{item.children?.length > 0 && <details><summary>Más opciones de {item.label}</summary>{item.children.map(child => link(child, true))}</details>}</div>)}</nav>
    </dialog>
  </header>;
}
