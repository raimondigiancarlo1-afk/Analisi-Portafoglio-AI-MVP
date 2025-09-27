
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

def build_pdf(path, header:str, items:list):
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    y = h - 2*cm
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, y, header)
    y -= 1*cm
    c.setFont("Helvetica", 10)
    for line in items:
        if y < 2*cm:
            c.showPage()
            y = h - 2*cm
            c.setFont("Helvetica", 10)
        c.drawString(2*cm, y, line[:110])
        y -= 0.6*cm
    c.save()
    return str(path)
