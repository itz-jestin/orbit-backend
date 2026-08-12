from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def create_pdf(report: str, filename: str):
    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    story = []

    for line in report.split("\n"):

        if line.strip():
            story.append(Paragraph(line, styles["BodyText"]))

    doc.build(story)