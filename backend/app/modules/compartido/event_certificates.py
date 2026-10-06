"""Constancias del portal basadas en asistencia verificada por coordinación."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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
