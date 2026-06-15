import tempfile
from pathlib import Path
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_pdf(expenses, filename=None):

    if filename is None:
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        filename = tmp_file.name
        tmp_file.close()
    else:
        filename = str(Path(filename).resolve())
        Path(filename).parent.mkdir(parents=True, exist_ok=True)

    c = canvas.Canvas(filename, pagesize=letter)
    page_number = 1

    def draw_header():
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, 755, "Expense Report")
        c.setFont("Helvetica", 10)
        c.drawString(50, 740, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        c.drawRightString(560, 740, f"Page {page_number}")
        c.line(50, 735, 560, 735)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, 715, "Date")
        c.drawString(140, 715, "Category")
        c.drawString(280, 715, "Description")
        c.drawRightString(560, 715, "Amount")

    draw_header()

    y = 695
    c.setFont("Helvetica", 11)
    total = 0

    if not expenses:
        c.drawString(50, y, "No expenses available.")
        y -= 20
    else:
        for e in expenses:
            if y < 80:
                c.showPage()
                page_number_value = page_number + 1
                page_number = page_number_value
                draw_header()
                y = 695
                c.setFont("Helvetica", 11)

            c.drawString(50, y, str(e.expense_date))
            c.drawString(140, y, str(e.category))
            c.drawString(280, y, str(e.description)[:40])
            c.drawRightString(560, y, f"{float(e.amount):.2f}")
            y -= 18
            total += float(e.amount)

    if y < 80:
        c.showPage()
        page_number += 1
        draw_header()
        y = 695

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, f"Total Spending: {total:.2f}")

    c.save()
    return filename