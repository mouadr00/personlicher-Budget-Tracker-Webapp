"""Report generation."""

from __future__ import annotations

import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .budget_service import MonthlySummary, TRANSFER_DIRECTION_ALIASES


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
            ("Monats-Cashflow", summary.cash_flow_chf),
            ("Saldo", summary.balance_chf),
            ("Budgetkonto", summary.budget_cash_chf),
            ("Sparkonto", summary.savings_balance_chf),
            ("Nettovermoegen", summary.net_worth_chf),
        ]:
            pdf.drawString(50, y, f"{label}: CHF {value:.2f}")
            y -= 22

        largest = summary.largest_expense_category or "Keine Ausgaben"
        pdf.drawString(50, y, f"Grösste Ausgabenkategorie: {largest} (CHF {summary.largest_expense_chf:.2f})")
        y -= 22
        pdf.drawString(50, y, f"Budget-Health: {summary.budget_health_score}/100 ({summary.budget_health_label})")
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
            y -= 18
            pdf.drawString(50, y, f"Umbuchung zum Sparkonto: CHF {summary.transfer_to_savings_chf:.2f}")
            y -= 18
            pdf.drawString(50, y, f"Umbuchung ins Budget: CHF {summary.transfer_to_budget_chf:.2f}")
            y -= 30

        pdf.setFont("Helvetica-Bold", 13)
        pdf.drawString(50, y, "Transaktionen")
        y -= 22
        pdf.setFont("Helvetica", 10)

        for transaction in summary.transactions[:28]:
            category = "Sparkonto" if transaction.kind == "Umbuchung" else (transaction.category.name if transaction.category else "Unbekannt")
            amount = transaction.signed_amount_chf
            normalized_direction = TRANSFER_DIRECTION_ALIASES.get(transaction.transfer_direction, transaction.transfer_direction)
            direction = f" | {normalized_direction}" if normalized_direction else ""
            line = f"{transaction.booking_date:%d.%m.%Y} | {transaction.kind}{direction} | {category} | CHF {amount:.2f}"
            pdf.drawString(50, y, line[:100])
            y -= 16
            if y < 60:
                pdf.showPage()
                y = height - 60
                pdf.setFont("Helvetica", 10)

        pdf.save()
        return path

    def create_monthly_csv(self, summary: MonthlySummary) -> Path:
        path = self.report_dir / f"budget_{summary.year}_{summary.month:02d}.csv"
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file, delimiter=";")
            writer.writerow(["Datum", "Typ", "Richtung", "Kategorie", "Notiz", "Betrag CHF"])
            for transaction in summary.transactions:
                category = "Sparkonto" if transaction.kind == "Umbuchung" else (transaction.category.name if transaction.category else "Unbekannt")
                direction = TRANSFER_DIRECTION_ALIASES.get(transaction.transfer_direction, transaction.transfer_direction or "")
                writer.writerow(
                    [
                        transaction.booking_date.isoformat(),
                        transaction.kind,
                        direction,
                        category,
                        transaction.note,
                        f"{transaction.signed_amount_chf:.2f}",
                    ]
                )
        return path
