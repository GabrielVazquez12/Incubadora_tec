import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import api from '../../shared/api/client.js';
import { usePortal } from '../../shared/portal/PortalContext.jsx';
import { usePortalRoute } from '../../shared/portal/PortalLayout.jsx';
import { Badge, Field, Form, Heading, Panel, Progress, Skeleton, Stats, Table, TextArea, formValues } from '../../shared/portal/ui.jsx';
import { money, today } from '../../shared/portal/data.js';
import { useAction, useRemote, downloadAsset } from '../innovatec/api.js';
import './route-workspace.css';

const sections = [
  ['diagnostico', 'Diagnóstico'], ['economia', 'Calculadora'], ['clasificacion', 'Clasificación'],
  ['ruta', 'Ruta de desarrollo'], ['formalizacion', 'Formalización'], ['seguimiento', 'Seguimiento'],
];
const stepStatuses = { pendiente: 'Pendiente', en_proceso: 'En proceso', en_revision: 'En revisión', completado: 'Cumplido con evidencia', no_aplica: 'No aplica' };
const taskStates = ['Pendiente', 'En proceso', 'Completada', 'Cancelada'];
const taskEvidenceStates = ['No enviada', 'Pendiente de revisión', 'Aprobada', 'Corrección requerida'];
const stateChoices = ['Registrado', 'Diagnóstico', 'Revisión económica', 'En desarrollo', 'En validación', 'En validación tecnológica', 'En formalización', 'En operación', 'Canalizado', 'Pausado', 'Abandonado', 'Concluido'];
const errorText = error => error?.response?.data?.detail || 'No fue posible guardar los cambios. Actualiza la página e inténtalo de nuevo.';
const emptyMoney = { inversion_inicial: '', costos_fijos: '', costo_variable_unitario: '', precio_venta: '', unidades_estimadas: '', observaciones: '' };

function routeTitle(value) {
  return ({ normal: 'Proyecto normal', tecnologica: 'Base tecnológica', no_seguro: 'Clasificación por confirmar' })[value] || 'Por clasificar';
}

export default function RouteWorkspace() {
  const { id } = useParams();
  const remote = useRemote(`/portal/incubadora/proyectos/${id}/ruta-emprendedora`, Boolean(id));
  const action = useAction();
  const portal = usePortal();
  const { role, base, userId } = usePortalRoute();
  const staff = role === 'admin' || portal.user?.perfil === 'asesor';
  const [route, setRoute] = useState(null), [section, setSection] = useState('diagnostico');
  const [data, setData] = useState({}), [dirty, setDirty] = useState(false), [saving, setSaving] = useState(false), [saveError, setSaveError] = useState('');
  const [calc, setCalc] = useState(emptyMoney), [answers, setAnswers] = useState({ depende_tecnologia: false, requiere_validacion_tecnica: false, activo_protegible: false });
  const [classification, setClassification] = useState({ tipo_proyecto: '', razon: '' });
  const version = useRef(0), ready = useRef(false), routeStateRef = useRef(null);
  const projectPath = staff ? `${base}/seguimiento/${id}` : `${base}/proyectos/${id}`;

  useEffect(() => {
    if (!remote.data) return;
    ready.current = true;
    version.current = remote.data.version || 0;
    routeStateRef.current = remote.data;
    setRoute(remote.data);
    setData(remote.data.datos || {});
    setAnswers(remote.data.respuestas_clasificacion || { depende_tecnologia: false, requiere_validacion_tecnica: false, activo_protegible: false });
    setClassification({ tipo_proyecto: remote.data.tipo_proyecto || remote.data.tipo_propuesto || '', razon: remote.data.razon_clasificacion || '' });
    setCalc(remote.data.calculadora?.[0]?.entradas || emptyMoney);
  }, [remote.data]);

  function acceptRoute(next) {
    if (!next || typeof next !== 'object' || next.version === undefined) return;
    version.current = next.version;
    routeStateRef.current = next;
    setRoute(next);
    setSaveError('');
  }

  useEffect(() => {
    if (!dirty || !ready.current || !id) return undefined;
    const snapshot = data;
    const timer = setTimeout(async () => {
      setSaving(true); setSaveError('');
      try {
        const response = await api.put(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/datos`, { datos: snapshot, version: version.current });
        acceptRoute(response.data);
        if (JSON.stringify(snapshot) === JSON.stringify(data)) setDirty(false);
      } catch (error) {
        setSaveError(errorText(error));
        if (error.response?.status === 409) remote.reload();
      } finally { setSaving(false); }
    }, 750);
    return () => clearTimeout(timer);
  }, [data, dirty, id]);

  const currentSteps = route?.plantillas || [];
  const branchSteps = currentSteps.filter(step => !step.codigo.startsWith('F'));
  const commonSteps = currentSteps.filter(step => step.codigo.startsWith('F'));
  const progress = useMemo(() => {
    const required = currentSteps.filter(step => step.obligatorio !== false);
    const complete = required.filter(step => ['completado', 'no_aplica'].includes(route?.pasos?.[step.codigo]?.estado)).length;
    return required.length ? Math.round(complete * 100 / required.length) : 0;
  }, [currentSteps, route?.pasos]);

  async function mutateRoute(path, payload, method = 'put', message = 'Cambios guardados.') {
    const result = await action.run(async () => (await api[method](path, payload)).data, message);
    if (!result) return null;
    acceptRoute(result.ruta || result);
    return result.ruta || result;
  }

  async function saveCalculation(event) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.post(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/calculos`, { ...fields, unidades_estimadas: Number(fields.unidades_estimadas) })).data, 'Cálculo guardado como una nueva versión.');
    if (result) acceptRoute(result.ruta);
  }

  async function saveClassification(event) {
    event.preventDefault();
    const fields = formValues(event);
    const values = {
      ...answers,
      tipo_proyecto: fields.tipo_proyecto,
      razon: fields.razon || '',
      version: version.current,
    };
    const result = await mutateRoute(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/clasificacion`, values, 'put', 'Clasificación guardada.');
    if (result) {
      setClassification({ tipo_proyecto: result.tipo_proyecto || '', razon: result.razon_clasificacion || '' });
      setAnswers(result.respuestas_clasificacion || answers);
    }
  }

  async function saveStep(event, code) {
    event.preventDefault();
    const fields = formValues(event);
    await mutateRoute(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/pasos/${code}`, {
      ...fields, documento_id: fields.documento_id || null, version: version.current,
    }, 'put', 'Avance del paso guardado.');
  }

  async function createTask(event) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.post(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/tareas`, { ...fields, responsable_id: fields.responsable_id, paso_codigo: fields.paso_codigo || '', descripcion: fields.descripcion || '' })).data, 'Tarea asignada.');
    if (result) remote.reload();
  }

  async function updateTask(event, task) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.put(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/tareas/${task.id}`, { ...fields, documento_id: fields.documento_id || null, version: task.version })).data, 'Evidencia enviada para revisión.');
    if (result) remote.reload();
  }

  async function reviewTask(event, task) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.put(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/tareas/${task.id}/revision`, { ...fields, version: task.version })).data, fields.decision === 'Aprobada' ? 'Evidencia aprobada.' : 'Se solicitó una corrección.');
    if (result) remote.reload();
  }

  async function createReferral(event) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.post(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/canalizaciones`, { ...fields, documento_id: fields.documento_id || null, paso_codigo: fields.paso_codigo || '' })).data, 'Canalización registrada; el seguimiento interno continúa.');
    if (result) remote.reload();
  }

  async function updateReferral(event, referral) {
    event.preventDefault();
    const fields = formValues(event);
    const result = await action.run(async () => (await api.put(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/canalizaciones/${referral.id}`, { ...fields, documento_id: fields.documento_id || null, version: referral.version })).data, 'Seguimiento de canalización actualizado.');
    if (result) remote.reload();
  }

  async function updateStatus(event) {
    event.preventDefault();
    const fields = formValues(event);
    await mutateRoute(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/estado`, { ...fields, cierre_administrativo: event.currentTarget.elements.cierre_administrativo.checked, version: version.current }, 'put', 'Estado actualizado.');
  }

  if (remote.loading && !route) return <Skeleton />;
  if (remote.error && !route) return <div className="route-workspace"><p role="alert" className="error">{remote.error}</p><Link to={projectPath}>Volver al expediente</Link></div>;
  if (!route) return <Skeleton />;

  const project = route.proyecto || portal.data.projects?.find(item => item.id === id);
  const latest = route.calculadora?.[0];
  const answerCount = Object.values(answers).filter(Boolean).length;
  const suggested = answerCount >= 2 ? 'tecnologica' : 'normal';
  const owner = project?.owner || project?.usuario_id;
  const people = (portal.data.users || []).filter(person => person.rol === 'admin' || person.id === owner || portal.data.members?.some(member => member.proyecto_id === id && member.usuario_id === person.id));

  return <main className="route-workspace">
    <Heading eyebrow="INCUBADORA DE EMPRESAS" title="Ruta emprendedora" description="Un paso a la vez: registra avances, evidencia y la próxima acción acordada." action={<Link className="button secondary" to={projectPath}>Volver al expediente</Link>} />
    <div className="route-summary"><div><span>Proyecto</span><strong>{project?.nombre || 'Expediente institucional'}</strong></div><div><span>Ruta</span><strong>{routeTitle(route.tipo_proyecto || route.tipo_propuesto)}</strong></div><div><span>Estado</span><strong>{route.estado}</strong></div><div className="route-progress"><span>Avance de pasos</span><Progress value={progress} /></div></div>
    <p className="route-disclaimer">El resultado económico es preliminar. Esta ruta orienta y da seguimiento; no reemplaza asesoría jurídica, fiscal o contable, validación técnica ni certificaciones.</p>
    {(remote.error || action.error || saveError) && <p role="alert" className="error">{remote.error || action.error || saveError}</p>}
    {(action.notice || saving) && <p role="status" className="notice">{saving ? 'Guardando avance…' : action.notice}</p>}
    <nav className="route-tabs" aria-label="Secciones de la ruta">
      {sections.map(([key, label]) => <button type="button" key={key} className={section === key ? 'active' : ''} aria-current={section === key ? 'step' : undefined} onClick={() => setSection(key)}>{label}</button>)}
    </nav>

    {section === 'diagnostico' && <Panel title="Diagnóstico del proyecto"><p>Cuéntanos el problema, quién lo vive y qué esperas validar. El avance se guarda automáticamente mientras escribes.</p><Form className="form-stack route-fields" onSubmit={event => { event.preventDefault(); setDirty(true); }}>
      <div className="form-grid"><Field label="Etapa inicial" name="etapa_inicial" value={data.etapa_inicial || 'idea'} onChange={event => { setData(value => ({ ...value, etapa_inicial: event.target.value })); setDirty(true); }}><option value="idea">Idea</option><option value="desarrollo">Desarrollo</option><option value="validacion">Validación</option><option value="formalizacion">Formalización</option><option value="operacion">Operación</option><option value="crecimiento">Crecimiento</option></Field><Field label="Estado de desarrollo" name="estado_desarrollo" value={data.estado_desarrollo || ''} onChange={event => { setData(value => ({ ...value, estado_desarrollo: event.target.value })); setDirty(true); }}><option value="">Selecciona</option><option>Idea</option><option>Prueba de concepto</option><option>Prototipo</option><option>Piloto</option><option>Producto</option></Field></div>
      {[
        ['problema', 'Problema o necesidad que atiende'], ['solucion', 'Solución o producto / servicio'], ['propuesta_valor', 'Propuesta de valor'],
        ['cliente_objetivo', 'Cliente o usuario objetivo'], ['mercado', 'Mercado y segmento prioritario'], ['alternativas', 'Alternativas existentes'],
      ].map(([key, label]) => <TextArea key={key} label={label} name={key} value={data[key] || ''} onChange={event => { setData(value => ({ ...value, [key]: event.target.value })); setDirty(true); }} />)}
    </Form><p className="route-saved-state">{saving ? 'Guardando…' : dirty ? 'Cambios pendientes de guardar.' : 'Todos los cambios están guardados.'}</p></Panel>}

    {section === 'economia' && <div className="route-grid"><Panel title="Supuestos mensuales"><p>Captura una versión nueva cada vez que cambien tus supuestos. Los cálculos anteriores quedan en el historial.</p><Form className="form-stack" onSubmit={saveCalculation} busy={action.busy}>
      <div className="form-grid"><Field label="Inversión inicial estimada (MXN)" name="inversion_inicial" type="number" min="0" step="0.01" required value={calc.inversion_inicial ?? ''} onChange={event => setCalc(value => ({ ...value, inversion_inicial: event.target.value }))} /><Field label="Costos fijos mensuales (MXN)" name="costos_fijos" type="number" min="0" step="0.01" required value={calc.costos_fijos ?? ''} onChange={event => setCalc(value => ({ ...value, costos_fijos: event.target.value }))} /><Field label="Costo variable por unidad (MXN)" name="costo_variable_unitario" type="number" min="0" step="0.01" required value={calc.costo_variable_unitario ?? ''} onChange={event => setCalc(value => ({ ...value, costo_variable_unitario: event.target.value }))} /><Field label="Precio por unidad (MXN)" name="precio_venta" type="number" min="0.01" step="0.01" required value={calc.precio_venta ?? ''} onChange={event => setCalc(value => ({ ...value, precio_venta: event.target.value }))} /><Field label="Unidades estimadas por mes" name="unidades_estimadas" type="number" min="0" step="1" required value={calc.unidades_estimadas ?? ''} onChange={event => setCalc(value => ({ ...value, unidades_estimadas: event.target.value }))} /></div>
      <TextArea label="Observaciones de estos supuestos" name="observaciones" maxLength={500} value={calc.observaciones || ''} onChange={event => setCalc(value => ({ ...value, observaciones: event.target.value }))} /><button className="button">Calcular y guardar versión</button>
    </Form></Panel><Panel title="Resultado actual">{latest ? <><div className={`route-light route-light-${latest.semaforo}`}><strong>{latest.semaforo === 'verde' ? 'Viabilidad preliminar' : latest.semaforo === 'amarillo' ? 'Viabilidad débil' : 'Revisar supuestos'}</strong><span>Versión {latest.version}</span></div><dl className="route-results">{[['Ingreso mensual', latest.resultados.ingreso_mensual], ['Costo variable mensual', latest.resultados.costo_variable_mensual], ['Costo total mensual', latest.resultados.costo_total_mensual], ['Utilidad estimada', latest.resultados.utilidad_mensual], ['Contribución unitaria', latest.resultados.contribucion_unitaria]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{money(value)}</dd></div>)}<div><dt>Punto de equilibrio</dt><dd>{latest.resultados.unidades_equilibrio_redondeadas ?? 'No definido'} {latest.resultados.unidades_equilibrio_redondeadas !== null ? 'unidades' : ''}</dd></div><div><dt>Margen estimado</dt><dd>{latest.resultados.margen_porcentaje === null ? 'No disponible' : `${latest.resultados.margen_porcentaje}%`}</dd></div><div><dt>Recuperación estimada</dt><dd>{latest.resultados.meses_recuperacion === null ? 'No calculable' : `${latest.resultados.meses_recuperacion} meses`}</dd></div></dl>{latest.resultados.causas?.map(reason => <p key={reason} className="route-cause">{reason}</p>)}<p className="helper">{latest.resultados.nota}</p></> : <p>Aún no hay cálculos guardados.</p>}</Panel>{(route.calculadora?.length || 0) > 1 && <Panel title="Historial de cálculos"><Table headings={['Versión', 'Fecha', 'Ingreso', 'Utilidad', 'Margen', 'Semáforo']}>{route.calculadora.map(item => <tr key={item.id}><td>{item.version}</td><td>{item.creado_en?.slice(0, 10)}</td><td>{money(item.resultados.ingreso_mensual)}</td><td>{money(item.resultados.utilidad_mensual)}</td><td>{item.resultados.margen_porcentaje ?? '—'}%</td><td><Badge>{item.semaforo}</Badge></td></tr>)}</Table></Panel>}</div>}

    {section === 'clasificacion' && <Panel title="¿Qué tipo de proyecto estás desarrollando?"><p>La ruta propone base tecnológica cuando dos o más respuestas sean “Sí”. La propuesta orienta el acompañamiento; coordinación puede confirmarla o cambiarla con justificación.</p>{!latest && <p className="helper">Primero guarda el análisis económico; después podrás registrar la clasificación.</p>}<Form className="form-stack" onSubmit={saveClassification} busy={action.busy}>
      {[
        ['depende_tecnologia', '¿La propuesta depende principalmente de software, hardware, ingeniería, ciencia o un proceso técnico especializado?'],
        ['requiere_validacion_tecnica', '¿Requiere prototipo, pruebas técnicas, laboratorio, certificación u homologación antes de escalar?'],
        ['activo_protegible', '¿Tiene tecnología, software, diseño, know-how o una invención que podría requerir protección?'],
      ].map(([key, question]) => <label className="route-question" key={key}><span>{question}</span><select value={answers[key] ? 'true' : 'false'} onChange={event => setAnswers(value => ({ ...value, [key]: event.target.value === 'true' }))}><option value="false">No</option><option value="true">Sí</option></select></label>)}
      <div className="route-proposal"><span>Propuesta automática</span><strong>{routeTitle(suggested)}</strong><small>{answerCount} respuestas afirmativas de 3</small></div>
      <Field label="Clasificación para la ruta" name="tipo_proyecto" value={classification.tipo_proyecto || suggested} onChange={event => setClassification(value => ({ ...value, tipo_proyecto: event.target.value }))}><option value="normal">Proyecto normal</option><option value="tecnologica">Base tecnológica</option><option value="no_seguro">No estoy seguro; abrir diagnóstico corto</option></Field>
      {(classification.tipo_proyecto === 'no_seguro' || staff) && <TextArea label={staff ? 'Justificación docente de la decisión' : '¿Qué necesitas aclarar con el docente?'} name="razon" required={classification.tipo_proyecto === 'no_seguro' || classification.tipo_proyecto !== suggested} value={classification.razon} onChange={event => setClassification(value => ({ ...value, razon: event.target.value }))} />}
      {!staff && <p className="helper">La clasificación distinta a la propuesta requiere revisión docente. Puedes guardar “No estoy seguro” para abrir un diagnóstico corto.</p>}
      <button className="button" disabled={!latest}>Guardar clasificación</button>
    </Form>{route.tipo_proyecto && <p className="route-current">Ruta activa: {routeTitle(route.tipo_proyecto)} · {route.clasificacion_confirmada ? 'Confirmada por docente' : 'Pendiente de confirmación docente'}</p>}</Panel>}

    {(section === 'ruta' || section === 'formalizacion') && <div className="route-step-list">
      {section === 'ruta' && !['normal', 'tecnologica'].includes(route.tipo_proyecto) && <Panel title="Confirma primero la ruta"><p>Completa las preguntas de clasificación para abrir la ruta normal o tecnológica. Si no estás seguro, coordinación puede ayudarte a elegirla.</p><button type="button" className="button secondary" onClick={() => setSection('clasificacion')}>Ir a clasificación</button></Panel>}
      {section === 'formalizacion' && <Panel title="Aplicabilidad de módulos"><p>Estas respuestas activan los requisitos pertinentes. Si respondes “No”, el módulo correspondiente no se agrega a la ruta.</p><div className="form-grid">{[['tiene_local', '¿El proyecto operará en un local físico?'], ['contratara_personal', '¿El proyecto contratará trabajadores?']].map(([key, label]) => <Field key={key} label={label} name={key} value={data[key] || ''} onChange={event => { setData(value => ({ ...value, [key]: event.target.value })); setDirty(true); }}><option value="">Selecciona</option><option value="si">Sí</option><option value="no">No</option></Field>)}</div><p className="route-saved-state">{saving ? 'Guardando…' : dirty ? 'Cambios pendientes de guardar.' : 'Todos los cambios están guardados.'}</p></Panel>}
      {(section === 'ruta' ? branchSteps : commonSteps).map(step => <RouteStep key={step.codigo} step={step} value={route.pasos?.[step.codigo] || {}} staff={staff} route={route} docs={portal.data.documents || []} projectId={id} onSubmit={saveStep} />)}
      {!route.clasificacion_confirmada && currentSteps.length > 0 && <Panel className="route-boundary"><p>La ruta propuesta ya está visible para avanzar en borrador. Coordinación debe confirmar la clasificación antes de aprobar pasos.</p><button type="button" className="button secondary" onClick={() => setSection('clasificacion')}>Revisar clasificación</button></Panel>}
      {section === 'formalizacion' && <Panel className="route-boundary"><p>Esta lista organiza decisiones y posibles requisitos. La incubadora registra y canaliza; las obligaciones se confirman con especialistas y autoridades competentes.</p></Panel>}
    </div>}

    {section === 'seguimiento' && <div className="route-step-list">
      <RouteNotifications projectId={id} staff={staff} />
      <Panel title="Tareas y evidencias"><p>Toda tarea tiene responsable, fecha objetivo y evidencia esperada. El docente aprueba o solicita corrección; quien entrega la evidencia no puede aprobarla.</p><Table headings={['Actividad', 'Responsable', 'Fecha objetivo', 'Estado', 'Evidencia', 'Revisión']} empty={!route.tareas?.length}>{route.tareas?.map(task => <tr key={task.id}><td>{task.nombre}{task.paso_codigo && <small>{task.paso_codigo}</small>}{task.descripcion && <small>{task.descripcion}</small>}</td><td>{portal.data.users?.find(person => person.id === task.responsable_id)?.nombre || 'Responsable asignado'}</td><td>{task.fecha_objetivo}{task.fecha_objetivo < today() && !['Completada', 'Cancelada'].includes(task.estado) && <Badge>Atrasada</Badge>}</td><td>{task.estado}</td><td>{task.evidencia_texto || (task.evidencia_url ? <a href={task.evidencia_url} target="_blank" rel="noopener noreferrer">Abrir enlace</a> : task.documento_id ? 'Documento en expediente' : 'Pendiente')}<small>{task.evidencia_esperada}</small></td><td>{task.estado_evidencia}{task.revision_notas && <small>{task.revision_notas}</small>}</td></tr>)}</Table>
        {staff && <details className="route-details"><summary>Asignar tarea</summary><Form className="form-stack route-fields" onSubmit={createTask} busy={action.busy}><Field label="Actividad" name="nombre" required maxLength={160} /><TextArea label="Descripción" name="descripcion" /><Field label="Paso relacionado" name="paso_codigo"><option value="">Seguimiento general</option>{currentSteps.map(step => <option value={step.codigo} key={step.codigo}>{step.codigo} · {step.titulo}</option>)}</Field><Field label="Responsable" name="responsable_id" required><option value="">Selecciona responsable</option>{people.map(person => <option key={person.id} value={person.id}>{person.nombre}</option>)}</Field><Field label="Fecha objetivo" name="fecha_objetivo" type="date" min={today()} required /><Field label="Evidencia que se espera" name="evidencia_esperada" required maxLength={1000} /><button className="button">Asignar tarea</button></Form></details>}
        {route.tareas?.filter(task => !staff && task.responsable_id === userId && !['Completada', 'Cancelada'].includes(task.estado)).map(task => <details key={`submit-${task.id}`} className="route-details"><summary>Enviar evidencia: {task.nombre}</summary><Form className="form-stack route-fields" onSubmit={event => updateTask(event, task)} busy={action.busy}><Field label="Estado" name="estado" defaultValue={task.estado}>{['Pendiente', 'En proceso'].map(value => <option key={value}>{value}</option>)}</Field><TextArea label="Evidencia o resultado" name="evidencia_texto" defaultValue={task.evidencia_texto || ''} /><Field label="Enlace de evidencia (opcional)" name="evidencia_url" type="url" maxLength={2000} defaultValue={task.evidencia_url || ''} /><Field label="Documento del expediente (opcional)" name="documento_id" defaultValue={task.documento_id || ''}><option value="">Sin documento</option>{(portal.data.documents || []).filter(document => document.proyecto_id === id).map(document => <option key={document.id} value={document.id}>{document.nombre}</option>)}</Field><button className="button">Enviar para revisión</button></Form></details>)}
        {staff && route.tareas?.filter(task => task.estado_evidencia === 'Pendiente de revisión').map(task => <details key={`review-${task.id}`} className="route-details"><summary>Revisar evidencia: {task.nombre}</summary><Form className="form-stack route-fields" onSubmit={event => reviewTask(event, task)} busy={action.busy}><p>{task.evidencia_texto || 'Sin nota'} {task.evidencia_url && <a href={task.evidencia_url} target="_blank" rel="noopener noreferrer">Abrir evidencia</a>}</p><Field label="Decisión" name="decision"><option>Aprobada</option><option>Corrección requerida</option></Field><TextArea label="Notas de revisión" name="notas" required /><button className="button">Guardar revisión</button></Form></details>)}
      </Panel>

      <Panel title="Canalización especializada"><p>La canalización conserva el seguimiento interno. Para cerrarla se debe registrar el resultado, la siguiente acción y evidencia de regreso.</p><Table headings={['Necesidad', 'Destino', 'Motivo', 'Fecha objetivo', 'Estado', 'Resultado / acción']} empty={!route.canalizaciones_ruta?.length}>{route.canalizaciones_ruta?.map(referral => <tr key={referral.id}><td>{referral.necesidad}</td><td>{referral.destino}<small>Qué llevar: {referral.informacion_usuario}</small></td><td>{referral.motivo}</td><td>{referral.fecha_objetivo}</td><td>{referral.estado}</td><td>{referral.resultado || 'Pendiente'}<small>{referral.siguiente_accion || 'Sin acción registrada'}</small></td></tr>)}</Table>
        {staff && <details className="route-details"><summary>Crear canalización</summary><Form className="form-stack route-fields" onSubmit={createReferral} busy={action.busy}><Field label="Necesidad detectada" name="necesidad" required maxLength={1000} /><TextArea label="Motivo" name="motivo" required /><Field label="Especialista o institución" name="destino" required maxLength={300} /><TextArea label="Información que debe llevar el usuario" name="informacion_usuario" required /><TextArea label="Resultado esperado" name="resultado_esperado" required /><Field label="Fecha objetivo" name="fecha_objetivo" type="date" min={today()} required /><Field label="Paso relacionado" name="paso_codigo"><option value="">Seguimiento general</option>{currentSteps.map(step => <option value={step.codigo} key={step.codigo}>{step.codigo} · {step.titulo}</option>)}</Field><Field label="Enlace de referencia (opcional)" name="evidencia_url" type="url" /><Field label="Documento del expediente (opcional)" name="documento_id"><option value="">Sin documento</option>{(portal.data.documents || []).filter(document => document.proyecto_id === id).map(document => <option key={document.id} value={document.id}>{document.nombre}</option>)}</Field><button className="button">Registrar canalización</button></Form></details>}
        {staff && route.canalizaciones_ruta?.filter(referral => referral.estado === 'Abierta').map(referral => <details key={`close-${referral.id}`} className="route-details"><summary>Registrar regreso de {referral.destino}</summary><Form className="form-stack route-fields" onSubmit={event => updateReferral(event, referral)} busy={action.busy}><Field label="Estado" name="estado"><option>Abierta</option><option>Cerrada</option><option>Cancelada</option></Field><TextArea label="Resultado o conclusión" name="resultado" /><TextArea label="Siguiente acción interna" name="siguiente_accion" /><TextArea label="Motivo de cancelación (si aplica)" name="motivo_cancelacion" /><Field label="Enlace de evidencia de regreso" name="evidencia_url" type="url" /><Field label="Documento con evidencia de regreso" name="documento_id"><option value="">Sin documento</option>{(portal.data.documents || []).filter(document => document.proyecto_id === id).map(document => <option key={document.id} value={document.id}>{document.nombre}</option>)}</Field><button className="button secondary">Actualizar canalización</button></Form></details>)}
      </Panel>

      {staff && <Panel title="Estado y cierre"><p>Los pasos obligatorios y las tareas deben estar completados antes de concluir. Coordinación puede hacer un cierre administrativo con motivo.</p><Form className="form-stack route-fields" onSubmit={updateStatus} busy={action.busy}><Field label="Nuevo estado" name="estado" defaultValue={route.estado}>{stateChoices.map(value => <option key={value}>{value}</option>)}</Field><TextArea label="Motivo o siguiente acción" name="motivo" maxLength={3000} /><label className="checkbox-label"><input type="checkbox" name="cierre_administrativo" />Cierre administrativo</label><button className="button">Actualizar estado</button></Form></Panel>}
    </div>}

    <footer className="route-footer"><button className="button secondary" type="button" disabled={action.busy} onClick={() => action.run(() => downloadAsset(`/portal/incubadora/proyectos/${id}/ruta-emprendedora/resumen.pdf`, 'resumen-ruta-emprendedora.pdf'), 'Resumen descargado.')}>Descargar resumen del expediente</button><Link to={projectPath}>Volver al expediente</Link></footer>
  </main>;
}

function RouteStep({ step, value, staff, route, docs, projectId, onSubmit }) {
  const current = value || {};
  if (!staff && ['completado', 'no_aplica'].includes(current.estado)) return <Panel className={`route-step route-step-${current.estado}`} title={`${step.codigo} · ${step.titulo}`}><p className="route-criterion">Criterio de salida: {step.criterio_salida}</p><Badge>{stepStatuses[current.estado]}</Badge>{current.respuesta && <p>{current.respuesta}</p>}{current.evidencia_texto && <p>{current.evidencia_texto}</p>}{current.evidencia_url && <p><a href={current.evidencia_url} target="_blank" rel="noopener noreferrer">Abrir evidencia</a></p>}{current.justificacion && <p className="helper">Justificación: {current.justificacion}</p>}</Panel>;
  return <Panel className={`route-step route-step-${current.estado || 'pendiente'}`} title={`${step.codigo} · ${step.titulo}`}><p className="route-criterion">Criterio de salida: {step.criterio_salida}</p><Badge>{stepStatuses[current.estado || 'pendiente']}</Badge><Form className="form-stack route-fields" onSubmit={event => onSubmit(event, step.codigo)}>
    <TextArea label="Respuesta o avance" name="respuesta" defaultValue={current.respuesta || ''} />
    <TextArea label="Evidencia textual" name="evidencia_texto" defaultValue={current.evidencia_texto || ''} />
    <div className="form-grid"><Field label="Enlace de evidencia (opcional)" name="evidencia_url" type="url" maxLength={2000} defaultValue={current.evidencia_url || ''} /><Field label="Documento del expediente (opcional)" name="documento_id" defaultValue={current.documento_id || ''}><option value="">Sin documento</option>{docs.filter(document => document.proyecto_id === projectId).map(document => <option key={document.id} value={document.id}>{document.nombre}</option>)}</Field></div>
    <Field label="Estado del paso" name="estado" defaultValue={staff ? (current.estado || 'pendiente') : (current.estado === 'en_revision' ? 'en_revision' : ['completado', 'no_aplica'].includes(current.estado) ? current.estado : current.estado || 'en_proceso')}>
      <option value="pendiente">Pendiente</option><option value="en_proceso">En proceso</option><option value="en_revision">Enviar a revisión</option>{staff && <><option value="completado">Cumplido con evidencia</option><option value="no_aplica">No aplica</option></>}{!staff && ['completado', 'no_aplica'].includes(current.estado) && <option value={current.estado} disabled>{stepStatuses[current.estado]}</option>}</Field>
    {staff && <TextArea label="Justificación docente (obligatoria para No aplica o salto de paso)" name="justificacion" defaultValue={current.justificacion || ''} />}
    <button className="button secondary">{staff ? 'Guardar y revisar paso' : 'Guardar avance'}</button>
  </Form>{current.justificacion && <p className="helper">Justificación registrada: {current.justificacion}</p>}</Panel>;
}

function RouteNotifications({ projectId, staff }) {
  const remote = useRemote(`/portal/incubadora/proyectos/${projectId}/ruta-emprendedora/notificaciones`);
  if (remote.loading || !remote.data?.items?.length) return null;
  return <Panel className="route-alerts" title="Próximas acciones"><ul>{remote.data.items.map((item, index) => <li key={`${item.tipo}-${item.tarea_id || item.canalizacion_id || index}`}><strong>{item.fecha}</strong> · {item.mensaje}</li>)}</ul><small>Los avisos aparecen dentro del portal al abrir este expediente.</small></Panel>;
}

export function RouteDashboard() {
  const [query, setQuery] = useState(''), portal = usePortal();
  const remote = useRemote(`/portal/incubadora/ruta-emprendedora/dashboard${query}`);
  const indicators = useRemote('/portal/incubadora/ruta-emprendedora/indicadores');
  return <main className="route-workspace"><Heading eyebrow="SEGUIMIENTO / INCUBADORA" title="Ruta emprendedora" description="Revisiones próximas, tareas, evidencias y canalizaciones abiertas." />{remote.error && <p role="alert" className="error">{remote.error}</p>}{remote.loading ? <Skeleton /> : <>
    <Panel title="Filtros"><Form className="filters" onSubmit={event => { event.preventDefault(); const values = formValues(event); const params = new URLSearchParams(Object.entries(values).filter(([, value]) => value)); setQuery(params.size ? `?${params}` : ''); }}><Field label="Tipo de proyecto" name="tipo_proyecto"><option value="">Todos</option><option value="normal">Normal</option><option value="tecnologica">Base tecnológica</option><option value="no_seguro">Por confirmar</option></Field><Field label="Etapa inicial" name="etapa"><option value="">Todas</option>{['idea', 'desarrollo', 'validacion', 'formalizacion', 'operacion', 'crecimiento'].map(value => <option key={value}>{value}</option>)}</Field><Field label="Estado" name="estado"><option value="">Todos</option>{stateChoices.map(value => <option key={value}>{value}</option>)}</Field><Field label="Asesor asignado" name="asesor_id"><option value="">Todos</option>{portal.data.users?.filter(person => person.perfil === 'asesor').map(person => <option key={person.id} value={person.id}>{person.nombre}</option>)}</Field><Field label="Desde" name="desde" type="date" /><Field label="Hasta" name="hasta" type="date" /><button className="button">Aplicar filtros</button></Form></Panel>
    <Stats items={[
      ['Proyectos con ruta', remote.data?.proyectos?.length || 0], ['Tareas atrasadas', remote.data?.tareas_atrasadas?.length || 0],
      ['Evidencias por revisar', remote.data?.evidencias_pendientes?.length || 0], ['Canalizaciones abiertas', remote.data?.canalizaciones_abiertas?.length || 0],
    ]} />
    {indicators.data && <Stats items={[
      ['Viabilidad preliminar en rojo', indicators.data.semaforos_actuales.rojo || 0],
      ['Viabilidad débil', indicators.data.semaforos_actuales.amarillo || 0],
      ['Viabilidad preliminar en verde', indicators.data.semaforos_actuales.verde || 0],
      ['Tareas completadas', `${indicators.data.porcentaje_tareas_completadas}%`],
      ['Rutas normales', indicators.data.tipos.normal || 0], ['Rutas tecnológicas', indicators.data.tipos.tecnologica || 0],
    ]} />}
    <Panel title="Proyectos"><Table headings={['Proyecto', 'Ruta', 'Etapa inicial', 'Estado', 'Asesor', 'Próxima revisión', 'Pasos cumplidos', 'Tareas atrasadas', 'Evidencias', 'Canalizaciones', 'Acción']} empty={!remote.data?.proyectos?.length}>{remote.data?.proyectos.map(item => <tr key={item.proyecto_id}><td>{item.nombre}{!item.clasificacion_confirmada && <small>Pendiente de confirmación docente</small>}</td><td>{routeTitle(item.tipo_proyecto)}</td><td>{item.etapa_inicial || 'Sin registrar'}</td><td>{item.estado}</td><td>{portal.data.users?.find(person => person.id === item.asesor_id)?.nombre || 'Sin asignar'}</td><td>{item.proxima_revision || 'Sin fecha'}</td><td>{item.pasos_completados}</td><td>{item.tareas_atrasadas}</td><td>{item.evidencias_pendientes}</td><td>{item.canalizaciones_abiertas}</td><td><Link to={`/coordinador/seguimiento/${item.proyecto_id}/ruta`}>Abrir ruta</Link></td></tr>)}</Table></Panel>
    <div className="route-grid"><Panel title="Tareas atrasadas"><Table headings={['Proyecto', 'Tarea', 'Responsable', 'Vence']} empty={!remote.data?.tareas_atrasadas?.length}>{remote.data?.tareas_atrasadas?.map(task => <tr key={task.id}><td>{task.proyecto_nombre}</td><td>{task.nombre}</td><td>{portal.data.users?.find(person => person.id === task.responsable_id)?.nombre || 'Responsable asignado'}</td><td>{task.fecha_objetivo}</td></tr>)}</Table></Panel><Panel title="Revisiones de esta semana"><Table headings={['Proyecto', 'Actividad', 'Fecha', 'Responsable']} empty={!remote.data?.proximas_revisiones?.length}>{remote.data?.proximas_revisiones?.map(task => <tr key={task.id}><td>{task.proyecto_nombre}</td><td>{task.nombre}</td><td>{task.fecha_objetivo}</td><td>{portal.data.users?.find(person => person.id === task.responsable_id)?.nombre || 'Responsable asignado'}</td></tr>)}</Table></Panel><Panel title="Evidencias pendientes"><Table headings={['Proyecto', 'Tarea', 'Evidencia', 'Acción']} empty={!remote.data?.evidencias_pendientes?.length}>{remote.data?.evidencias_pendientes?.map(task => <tr key={task.id}><td>{task.proyecto_nombre}</td><td>{task.nombre}</td><td>{task.evidencia_texto || (task.evidencia_url ? <a href={task.evidencia_url} target="_blank" rel="noopener noreferrer">Abrir enlace</a> : 'Documento')}</td><td><Link to={`/coordinador/seguimiento/${task.proyecto_id}/ruta`}>Revisar</Link></td></tr>)}</Table></Panel></div>
    <Panel title="Proyectos sin actividad"><Table headings={['Proyecto', 'Estado', 'Asesor', 'Último movimiento']} empty={!remote.data?.sin_actividad?.length}>{remote.data?.sin_actividad?.map(item => <tr key={item.proyecto_id}><td>{item.nombre}</td><td>{item.estado}</td><td>{portal.data.users?.find(person => person.id === item.asesor_id)?.nombre || 'Sin asignar'}</td><td>{item.actualizado_en?.slice(0, 10) || 'Sin registro'}</td></tr>)}</Table></Panel>
    <Panel title="Canalizaciones abiertas"><Table headings={['Proyecto', 'Necesidad', 'Destino', 'Fecha objetivo', 'Resultado']} empty={!remote.data?.canalizaciones_abiertas?.length}>{remote.data?.canalizaciones_abiertas?.map(referral => <tr key={referral.id}><td>{referral.proyecto_nombre}</td><td>{referral.necesidad}</td><td>{referral.destino}</td><td>{referral.fecha_objetivo}</td><td>{referral.resultado || 'Pendiente'}</td></tr>)}</Table></Panel>
    </>}
  </main>;
}

export function RouteSettings() {
  const remote = useRemote('/portal/incubadora/configuracion-ruta');
  const action = useAction();
  const [config, setConfig] = useState(null);
  useEffect(() => { if (remote.data) setConfig(remote.data); }, [remote.data]);
  async function save(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = formValues(event);
    const templates = structuredClone(config.plantillas_ruta);
    for (const kind of ['normal', 'tecnologica', 'comun']) for (const step of templates[kind]) {
      step.titulo = form.elements[`titulo-${step.codigo}`].value.trim();
      step.criterio_salida = form.elements[`criterio-${step.codigo}`].value.trim();
      step.orden = Number(form.elements[`orden-${step.codigo}`].value);
    }
    const payload = { margen_minimo: fields.margen_minimo, meses_recuperacion_max: Number(fields.meses_recuperacion_max), dias_inactividad: fields.dias_inactividad ? Number(fields.dias_inactividad) : null, plantillas_ruta: templates, version: config.version };
    const result = await action.run(async () => (await api.put('/portal/incubadora/configuracion-ruta', payload)).data, 'Configuración de la ruta actualizada.');
    if (result) setConfig(result);
  }
  if (remote.loading && !config) return <Skeleton />;
  if (!config) return <p role="alert" className="error">{remote.error || 'No se pudo cargar la configuración.'}</p>;
  return <main className="route-workspace"><Heading eyebrow="COORDINACIÓN / CONFIGURACIÓN" title="Configuración de la ruta" description="Ajusta criterios de salida y umbrales económicos sin cambiar el código." />{remote.error && <p role="alert" className="error">{remote.error}</p>}{action.error && <p role="alert" className="error">{action.error}</p>}{action.notice && <p role="status" className="notice">{action.notice}</p>}<Form className="form-stack" onSubmit={save} busy={action.busy}><Panel title="Umbrales económicos"><div className="form-grid"><Field label="Margen mínimo (%)" name="margen_minimo" type="number" min="0" max="100" step="0.1" required defaultValue={config.margen_minimo} /><Field label="Recuperación máxima (meses)" name="meses_recuperacion_max" type="number" min="1" max="600" step="1" required defaultValue={config.meses_recuperacion_max} /><Field label="Días sin actividad para alertar" name="dias_inactividad" type="number" min="1" max="3650" defaultValue={config.dias_inactividad || ''} /></div></Panel>
    {[
      ['normal', 'Ruta normal'], ['tecnologica', 'Ruta de base tecnológica'], ['comun', 'Formalización común'],
    ].map(([kind, title]) => <Panel key={kind} title={title}><div className="route-settings-list">{config.plantillas_ruta[kind].map(step => <div className="route-settings-step" key={step.codigo}><strong>{step.codigo}</strong><Field label="Nombre del paso" name={`titulo-${step.codigo}`} required maxLength={160} defaultValue={step.titulo} /><TextArea label="Criterio de salida" name={`criterio-${step.codigo}`} required maxLength={1000} defaultValue={step.criterio_salida} /><Field label="Orden" name={`orden-${step.codigo}`} type="number" min="1" max="100" step="1" required defaultValue={step.orden} /></div>)}</div></Panel>)}<p className="helper">Los pasos de la guía permanecen activos y obligatorios. Puedes adaptar su nombre, criterio y orden a los acuerdos institucionales.</p><button className="button">Guardar configuración</button></Form></main>;
}
