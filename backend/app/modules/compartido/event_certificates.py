"""Constancias del portal basadas en asistencia verificada por coordinación."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.platypus import Image
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo


def build_event_certificate(registration, event, participant):
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=landscape(A4), rightMargin=70, leftMargin=70,
                                topMargin=55, bottomMargin=45, title="Constancia de participación",
                                author="Incubadora ITS")
    styles = {
        "brand": ParagraphStyle("brand", fontName="Helvetica-Bold", fontSize=13, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#70223d")),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=27, leading=33, alignment=TA_CENTER, textColor=colors.HexColor("#70223d")),
        "name": ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=22, leading=29, alignment=TA_CENTER),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=13, leading=20, alignment=TA_CENTER),
        "small": ParagraphStyle("small", fontName="Helvetica", fontSize=9, leading=13, alignment=TA_CENTER, textColor=colors.HexColor("#615966")),
    }
    text = lambda value, style: Paragraph(escape(str(value)), styles[style])
    contents = [text("Tecnológico de Saltillo | Incubadora en Línea", "brand"), Spacer(1, 25),
                text("Constancia de participación", "title"), Spacer(1, 23), text("Se hace constar la participación de", "body"),
                Spacer(1, 12), text(participant.nombre, "name"), Spacer(1, 16), text("en la actividad", "body"),
                text(event.nombre, "name"), Spacer(1, 14),
                text(f"Fecha: {event.fecha.strftime('%d/%m/%Y')} | Modalidad: {event.modalidad}", "body"),
                Spacer(1, 20), text("Asistencia verificada por coordinación en el portal de la incubadora.", "small"),
                text(f"Folio: {registration.id}", "small"),
                text("Documento generado por el portal. No incluye firmas ni sellos institucionales.", "small")]
    document.build(contents)
    return output.getvalue()


def build_innovatec_diploma(team, convocatoria, proposal, member):
    """Digital recognition, authorized by coordination; no invented signatures."""
    output = BytesIO()
    document = SimpleDocTemplate(output, pagesize=A4, leftMargin=70, rightMargin=70,
                                topMargin=90, bottomMargin=45, title='Diploma InnovaTec',
                                author='Enlaces Institucionales ITS')
    primary = colors.HexColor('#700020')
    styles = {
        'title': ParagraphStyle('diploma-title', fontName='Times-Bold', fontSize=25, leading=31, alignment=TA_CENTER, textColor=primary),
        'name': ParagraphStyle('diploma-name', fontName='Helvetica-Bold', fontSize=20, leading=27, alignment=TA_CENTER),
        'body': ParagraphStyle('diploma-body', fontName='Helvetica', fontSize=12, leading=18, alignment=TA_CENTER),
        'small': ParagraphStyle('diploma-small', fontName='Helvetica', fontSize=9, leading=13, alignment=TA_CENTER),
    }
    paragraph = lambda value, style='body': Paragraph(escape(str(value)), styles[style])
    logo = Path(__file__).resolve().parents[2] / 'assets' / 'enlaces-institucionales.jpeg'
    role = 'asesor docente' if member.tipo == 'asesor' else 'participante'
    issued = datetime.now(ZoneInfo('America/Mexico_City')).strftime('%d/%m/%Y')
    document.build([
        Image(str(logo), width=150, height=150), Spacer(1, 90),
        paragraph('Diploma de participación', 'title'), Spacer(1, 18),
        paragraph('Se reconoce a'), Spacer(1, 12), paragraph(member.nombre, 'name'), Spacer(1, 18),
        paragraph(f'como {role} del proyecto'), paragraph(proposal.datos['nombre'], 'name'), Spacer(1, 18),
        paragraph(f'InnovaTec — proceso local del Instituto Tecnológico de Saltillo, {convocatoria.anio}.'),
        Spacer(1, 24), paragraph(f'Equipo: {proposal.datos["equipo"]}'),
        paragraph(f'Folio: {team.folio} / {member.id}', 'small'),
        paragraph(f'Emisión del portal: {issued}', 'small'), Spacer(1, 16),
        paragraph('Documento generado por el portal. No incluye firmas ni sellos institucionales.', 'small'),
    ])
    return output.getvalue()
