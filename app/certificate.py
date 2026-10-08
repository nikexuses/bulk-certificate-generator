from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


OUTPUT_DIR = Path("certificates")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_certificate(
    recipient_name: str,
    event_name: str,
    certificate_title: str,
    certificate_id: int
) -> str:

    filename = f"certificate_{certificate_id}.pdf"
    output_path = OUTPUT_DIR / filename

    page_width, page_height = landscape(A4)

    pdf = canvas.Canvas(
        str(output_path),
        pagesize=landscape(A4)
    )

    # Border
    pdf.setStrokeColor(colors.HexColor("#1F4E79"))
    pdf.setLineWidth(4)

    pdf.rect(
        30,
        30,
        page_width - 60,
        page_height - 60
    )

    # Inner border
    pdf.setStrokeColor(colors.HexColor("#D4AF37"))
    pdf.setLineWidth(1)

    pdf.rect(
        42,
        42,
        page_width - 84,
        page_height - 84
    )

    # Title
    pdf.setFillColor(colors.HexColor("#1F4E79"))
    pdf.setFont("Helvetica-Bold", 30)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 130,
        certificate_title
    )

    # Subtitle
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 15)

    pdf.drawCentredString(
        page_width / 2,
        page_height - 175,
        "This certificate is proudly presented to"
    )

    # Recipient name
    pdf.setFillColor(colors.HexColor("#D4AF37"))
    pdf.setFont("Helvetica-Bold", 32)

    pdf.drawCentredString(
        page_width / 2,
        page_height / 2 + 35,
        recipient_name
    )

    # Event information
    pdf.setFillColor(colors.black)
    pdf.setFont("Helvetica", 16)

    pdf.drawCentredString(
        page_width / 2,
        page_height / 2 - 15,
        f"for successfully participating in {event_name}"
    )

    # Certificate ID
    pdf.setFont("Helvetica", 10)

    pdf.drawCentredString(
        page_width / 2,
        75,
        f"Certificate ID: {certificate_id}"
    )

    pdf.save()

    return str(output_path)
