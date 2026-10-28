import { Heading, Panel } from '../portal/ui.jsx';

export default function PendingModule({ title }) {
  return <section className="pending-module"><Heading eyebrow="ENLACES INSTITUCIONALES ITS" title={title} description="Configuración institucional pendiente." /><Panel><p>[Por definir: configuración y operación de {title.toLocaleLowerCase('es-MX')}]</p></Panel></section>;
}
