from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()

def generate_pdf(report, filename):

    doc = SimpleDocTemplate(filename)

    elements = []

    for line in report.split("\n"):

        line = line.strip()

        if not line:
            elements.append(Spacer(1, 12))
            continue

        if line.startswith("#"):

            text = line.replace("#", "").strip()

            elements.append(
                Paragraph(
                    f"<b>{text}</b>",
                    styles["Heading1"]
                )
            )

        else:

            elements.append(
                Paragraph(
                    line,
                    styles["BodyText"]
                )
            )

    doc.build(elements)

    return filename