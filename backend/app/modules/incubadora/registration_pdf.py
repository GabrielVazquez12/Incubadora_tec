from io import BytesIO
from pathlib import Path
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
