from io import BytesIO
from pathlib import Path
from datetime import datetime
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle


def build_diagnostic_pdf(diagnostic, owner, name):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=80, bottomMargin=54, title='Registro y diagnóstico de Incubadora', author='Enlaces Institucionales ITS')
    style = ParagraphStyle('diagnostic-body', fontName='Helvetica', fontSize=10, leading=14)
    title = ParagraphStyle('diagnostic-title', fontName='Times-Bold', fontSize=20, leading=25, spaceAfter=18, textColor=colors.HexColor('#700020'))
    paragraph = lambda value: Paragraph(escape(str(value)).replace('\n', '<br/>'), style)
    logo = Path(__file__).resolve().parents[2] / 'assets' / 'enlaces-institucionales.jpeg'
    labels = {'telefono': 'Teléfono', 'tipo_usuario': 'Tipo de usuario', 'carrera': 'Carrera', 'semestre': 'Semestre', 'perfil': 'Perfil del proyecto', 'etapa': 'Etapa', 'descripcion': 'Idea o negocio y situación actual', 'estado_actual': 'Estado actual', 'necesidades': 'Necesidades', 'canal_llegada': 'Canal de llegada', 'proyecto_pausado': '¿Ha pausado un proyecto?', 'motivo_pausa': 'Motivo de pausa', 'frecuencia': 'Frecuencia de seguimiento', 'modalidad': 'Modalidad de asesoría'}
    rows = [[paragraph('Nombre'), paragraph(owner.nombre)], [paragraph('Correo'), paragraph(owner.correo)], [paragraph('Proyecto'), paragraph(name)]]
    for key, label in labels.items():
        value = diagnostic.datos.get(key)
        if isinstance(value, list):
            value = '; '.join(value)
        elif isinstance(value, bool):
            value = 'Sí' if value else 'No'
        rows.append([paragraph(label), paragraph(value if value is not None and value != '' else 'No aplica')])
    table = Table(rows, colWidths=[145, A4[0] - 108 - 145], hAlign='LEFT', splitByRow=1, splitInRow=1)
    table.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#dddddd')), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica', 8)
        canvas.drawString(54, 30, f'Registro {diagnostic.id} | versión {diagnostic.version}')
        canvas.drawRightString(A4[0] - 54, 30, f'Página {doc.page}')
        canvas.restoreState()
    document.build([Image(str(logo), width=140, height=140), Spacer(1, 80), Paragraph('Registro y diagnóstico inicial', title), table, Spacer(1, 16), paragraph(f'Consentimiento registrado: {diagnostic.consentimiento["fecha"]}; versión del aviso: {diagnostic.consentimiento["version"]}.'), paragraph('Registro generado por el portal. No incluye firmas ni sellos institucionales.')], onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()


def build_route_summary_pdf(project, route):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=54, rightMargin=54, topMargin=54, bottomMargin=54, title='Resumen de ruta emprendedora', author='Incubadora de Empresas ITS')
    body = ParagraphStyle('route-body', fontName='Helvetica', fontSize=9, leading=13)
    title = ParagraphStyle('route-title', fontName='Times-Bold', fontSize=20, leading=25, spaceAfter=10, textColor=colors.HexColor('#700020'))
    heading = ParagraphStyle('route-heading', fontName='Helvetica-Bold', fontSize=12, leading=16, spaceBefore=10, spaceAfter=5, textColor=colors.HexColor('#34434d'))
    paragraph = lambda value: Paragraph(escape(str(value if value not in (None, '') else 'Pendiente')).replace('\n', '<br/>'), body)
    story = [Paragraph('Ruta emprendedora', title), paragraph(f'Proyecto: {project.nombre}'), paragraph(f'Estado: {route.get("estado", "Registrado")}'), paragraph(f'Clasificación: {route.get("tipo_proyecto") or route.get("tipo_propuesto") or "Pendiente de revisión"}'), paragraph('La ruta es una guía de acompañamiento. No sustituye asesoría jurídica, fiscal, contable ni certificación profesional.'), Spacer(1, 10)]
    story.append(Paragraph('Diagnóstico y datos del proyecto', heading))
    rows = [[paragraph('Campo'), paragraph('Respuesta')]]
    labels = {
        'etapa_inicial': 'Etapa inicial', 'problema': 'Problema', 'solucion': 'Solución',
        'propuesta_valor': 'Propuesta de valor', 'cliente_objetivo': 'Cliente objetivo',
        'mercado': 'Mercado', 'modelo_ingresos': 'Modelo de ingresos',
        'evidencia_validacion': 'Validación comercial', 'estado_desarrollo': 'Estado de desarrollo',
    }
    for key, label in labels.items():
        rows.append([paragraph(label), paragraph((route.get('datos') or {}).get(key))])
    table = Table(rows, colWidths=[140, A4[0] - 108 - 140], repeatRows=1, splitByRow=1, splitInRow=1)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef1f2')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#d7dddf')), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(table)
    latest = (route.get('calculadora') or [None])[0]
    story.append(Paragraph('Revisión económica', heading))
    if latest:
        story.extend([paragraph(f'Versión {latest["version"]} · Semáforo: {latest["semaforo"].capitalize()}'), paragraph(f'Ingreso mensual: {latest["resultados"].get("ingreso_mensual")} · Costo total: {latest["resultados"].get("costo_total_mensual")} · Utilidad estimada: {latest["resultados"].get("utilidad_mensual")}'), paragraph(f'Margen: {latest["resultados"].get("margen_porcentaje")} % · Punto de equilibrio: {latest["resultados"].get("unidades_equilibrio_redondeadas")} unidades · Recuperación: {latest["resultados"].get("meses_recuperacion")} meses'), paragraph(latest['resultados'].get('nota'))])
    else:
        story.append(paragraph('No se ha guardado un cálculo.'))
    story.append(Paragraph('Ruta y evidencias', heading))
    steps = route.get('plantillas') or []
    progress = route.get('pasos') or {}
    rows = [[paragraph('Paso'), paragraph('Estado'), paragraph('Respuesta / evidencia')]]
    for step in steps:
        saved = progress.get(step['codigo'], {})
        evidence = saved.get('respuesta') or saved.get('evidencia_texto') or saved.get('evidencia_url') or saved.get('justificacion')
        rows.append([paragraph(f'{step["codigo"]} · {step["titulo"]}'), paragraph(saved.get('estado', 'pendiente')), paragraph(evidence)])
    table = Table(rows, colWidths=[160, 80, A4[0] - 108 - 240], repeatRows=1, splitByRow=1, splitInRow=1)
    table.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#eef1f2')), ('VALIGN', (0, 0), (-1, -1), 'TOP'), ('LINEBELOW', (0, 0), (-1, -1), .3, colors.HexColor('#d7dddf')), ('TOPPADDING', (0, 0), (-1, -1), 5), ('BOTTOMPADDING', (0, 0), (-1, -1), 5)]))
    story.append(table)
    story.append(Paragraph('Tareas y canalizaciones', heading))
    for task in route.get('tareas', []):
        story.append(paragraph(f'Tarea: {task["nombre"]} · {task["estado"]} · vence {task["fecha_objetivo"]} · evidencia esperada: {task["evidencia_esperada"]}'))
    for referral in route.get('canalizaciones_ruta', []):
        story.append(paragraph(f'Canalización a {referral["destino"]} · {referral["estado"]} · resultado: {referral["resultado"] or "pendiente"} · siguiente acción: {referral["siguiente_accion"] or "pendiente"}'))
    story.append(Spacer(1, 12))
    story.append(paragraph(f'Generado: {datetime.now().astimezone().isoformat(timespec="minutes")} · Proyecto {project.id}'))
    document.build(story)
    return output.getvalue()
