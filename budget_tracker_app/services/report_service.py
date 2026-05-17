"""Report generation."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .budget_service import MonthlySummary


class ReportService:
    """Creates a compact monthly PDF report."""

    def __init__(self, report_dir: str = "./data/reports") -> None:
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def create_monthly_pdf(self, summary: MonthlySummary) -> Path:
        path = self.report_dir / f"budget_{summary.year}_{summary.month:02d}.pdf"
        pdf = canvas.Canvas(str(path), pagesize=A4)
        width, height = A4
        y = height - 60

        pdf.setFont("Helvetica-Bold", 18)
        pdf.drawString(50, y, f"Budgetbericht {summary.month:02d}/{summary.year}")
        y -= 40

        pdf.setFont("Helvetica", 12)
        for label, value in [
            ("Einnahmen", summary.income_chf),
            ("Ausgaben", summary.expenses_chf),
            ("Saldo", summary.balance_chf),
        ]:
            pdf.drawString(50, y, f"{label}: CHF {value:.2f}")
            y -= 22

        largest = summary.largest_expense_category or "Keine Ausgaben"
        pdf.drawString(50, y, f"Groesste Ausgabenkategorie: {largest} (CHF {summary.largest_expense_chf:.2f})")
        y -= 35

        if summary.plan:
            pdf.setFont("Helvetica-Bold", 13)
            pdf.drawString(50, y, "Budgetplan")
            y -= 22
            pdf.setFont("Helvetica", 11)
            pdf.drawString(50, y, f"Geplante Einnahmen: CHF {summary.plan.planned_income_chf:.2f}")
            y -= 18
            pdf.drawString(50, y, f"Geplante Ausgaben: CHF {summary.plan.planned_expenses_chf:.2f}")
            y -= 18
            pdf.drawString(50, y, f"Sparziel: CHF {summary.plan.savings_goal_chf:.2f}")
            y -= 30

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, y, "Transaktionen")
        y -= 22
        pdf.setFont("Helvetica", 10)

        for transaction in summary.transactions[:28]:
            category = transaction.category.name if transaction.category else "Unbekannt"
            amount = transaction.signed_amount_chf
            line = f"{transaction.booking_date:%d.%m.%Y} | {transaction.kind} | {category} | CHF {amount:.2f}"
            pdf.drawString(50, y, line[:100])
            y -= 16
            if y < 60:
                pdf.showPage()
                y = height - 60
                pdf.setFont("Helvetica", 10)

        pdf.save()
        return path
