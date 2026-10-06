import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { usePortal } from '../portal/PortalContext.jsx';
import { usePortalRoute } from '../portal/PortalLayout.jsx';
import { dateLabel, money } from '../portal/data.js';
import { Empty, Heading, Panel } from '../portal/ui.jsx';
import { occupied, closed } from './helpers.js';

export function Checkout() {
  const { id } = useParams();
  const { data } = usePortal(); 
  const { base, userId } = usePortalRoute();
  
  const [error, setError] = useState('');
  
  const event = data.events.find(e => e.id === id);
  if (!event) return <Empty>Evento no encontrado.</Empty>;
  
  const registered = data.registrations.some(r => r.event === id && r.user === userId);
  const unavailable = registered || closed(event) || occupied(data, event) >= event.cupo;
  
  async function pay(e) {
    e.preventDefault();
    if (unavailable) return;
    
    try {
      // 1. Obtenemos el token de la sesión (asumiendo que se guarda en localStorage)
      const token = localStorage.getItem('token'); 
      const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      
      // 2. Pedimos al backend que genere el link de Stripe
      const response = await fetch(`${API_URL}/portal/events/${id}/checkout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        }
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || 'Error al iniciar el pago.');
      }
      
      const session = await response.json();
      
      // 3. Redirigimos al usuario a la ventana de cobro de Stripe
      window.location.href = session.url; 
      
    } catch (err) {
      setError(err.message);
    }
  }
  
  return (
    <>
      <Heading title="Confirma tu inscripción" description="Revisa los detalles de tu actividad antes de continuar." />
      <ol className="checkout-steps">
        <li>1 · Seleccionar evento</li>
        <li className="active">2 · Confirmar datos</li>
        <li>3 · Pago</li>
        <li>4 · Comprobante</li>
      </ol>
      <div className="two-columns">
        <Panel title={event.nombre}>
          <p className="muted">{dateLabel(event.fecha)} · {event.hora} · {event.modalidad}</p>
          <p>{event.descripcion}</p>
          <hr />
          <div className="row between">
            <strong>Total de inscripción</strong>
            <strong className="checkout-total">{money(event.precio)} <small>MXN</small></strong>
          </div>
          <p className="helper">La inscripción incluye acceso a la actividad en la fecha y modalidad indicadas.</p>
        </Panel>
        
        <Panel title="Método de pago">
          <form className="form-stack" onSubmit={pay}>
            <div className="payment-method">Pago con Tarjeta (Stripe)</div>
            <p className="info-box">Serás redirigido a una pasarela de pago segura para introducir tus datos bancarios.</p>
            
            <label className="checkbox-label">
              <input type="checkbox" required /> Revisé el evento, su fecha y el importe.
            </label>
            
            {error && <p className="error" role="alert">{error}</p>}
            
            {unavailable && (
              <p role="status">
                {registered ? 'Ya tienes una inscripción para este evento.' : 'El evento ya no está disponible o no tiene cupo.'}
              </p>
            )}
            
            <button className="button" disabled={unavailable}>
              Pagar inscripción
            </button>
            <Link className="text-link" to={`${base}/eventos`}>← Volver a los eventos</Link>
          </form>
        </Panel>
      </div>
    </>
  );
}