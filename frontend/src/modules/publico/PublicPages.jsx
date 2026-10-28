import { Link } from 'react-router-dom';
import PublicLayout from './PublicLayout.jsx';
import Newsletter from './Newsletter.jsx';
import { Stepper } from '../../shared/portal/ui.jsx';

export const innovationSteps = ['Recepción de la convocatoria desde México', 'Lectura y análisis del manual de operaciones del año en curso', 'Difusión de la convocatoria', 'Día de Enlaces', 'Inscripción a InnovaTec', 'Recepción de la documentación de cada equipo', 'Coordinación de la etapa local', 'Entrega de diplomas a participantes y asesores', 'Seguimiento de los equipos acreditados', 'Logística para etapas regional y nacional', 'Continuidad en la Incubadora de Empresas y la plataforma de InnovaTec'];

export default function PublicPage({ section }) {
  const content = {
    incubadora: ['Incubadora de Empresas', 'Diagnosticar, entender, diseñar.', <><p>Registro y diagnóstico, asesoría personalizada y seguimiento para ideas y negocios. La atención debe concluir con una actividad acordada, un responsable y una fecha de revisión.</p><ol className="institutional-stepper">{['Diagnosticar', 'Validar', 'Vender', 'Formalizar y seguir'].map(stage => <li key={stage}><h2>{stage}</h2><p>[Por definir: servicios y resultados institucionales validados]</p></li>)}</ol><Link className="button" to="/registro">Quiero registrar mi proyecto</Link><p className="helper">El registro actual comienza con la creación de una cuenta.</p></>],
    innovatec: ['InnovaTec', 'Proceso local del Instituto Tecnológico de Saltillo.', <><Stepper steps={innovationSteps} label="Proceso local InnovaTec en once pasos" /><p>[Por definir: convocatoria y manual vigentes, requisitos, fechas y sedes]</p><Link className="button" to="/innovatecnm/registros">Acceder al registro interno</Link><p className="helper">El registro interno existente requiere una cuenta con acceso al módulo.</p></>],
    vinculacion: ['Vinculación', 'Orientación y contacto institucional.', <p>[Por definir: acciones de vinculación y contacto institucional]</p>],
    contacto: ['Contacto', 'Enlaces Institucionales ITS', <><p>[Por definir: correo de contacto]</p><p>[Por definir: teléfono]</p><p>[Por definir: horario de atención]</p><p>Instituto Tecnológico de Saltillo</p></>],
    privacidad: ['Aviso de privacidad', 'Protección de datos personales.', <p>[Por definir: aviso de privacidad institucional aprobado, responsable, versión y plazo de conservación]</p>],
    encuestas: ['Encuestas', 'Información, orientación y necesidades de la comunidad.', <p>[Por definir: encuesta habilitada y configuración de respuesta anónima o identificada]</p>],
    eventos: ['Eventos', 'Actividades de la comunidad institucional.', <Newsletter />],
  }[section];
  return <PublicLayout><section className="public-information landing-container"><p className="landing-eyebrow">Enlaces Institucionales ITS</p><h1>{content[0]}</h1><p className="landing-lead">{content[1]}</p>{content[2]}</section></PublicLayout>;
}
