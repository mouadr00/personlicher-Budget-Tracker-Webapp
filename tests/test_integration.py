def test_integration_single_booking_creates_summary_and_pdf(budget_service, report_service):
    budget_service.add_transaction("2030-05-01", "Einnahme", "Gehalt", "3500.00", "Lohn")

    summary = budget_service.monthly_summary(2030, 5)
    pdf_path = report_service.create_monthly_pdf(summary)

    assert summary.income_chf == 3500.00
    assert summary.balance_chf == 3500.00
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0


def test_integration_multiple_bookings_calculate_monthly_budget_correctly(budget_service):
    budget_service.add_transaction("2030-05-01", "Einnahme", "Gehalt", "4200.00")
    budget_service.add_transaction("2030-05-02", "Ausgabe", "Miete", "1500.00")
    budget_service.add_transaction("2030-05-03", "Ausgabe", "Freizeit", "150.25")

    summary = budget_service.monthly_summary(2030, 5)

    assert summary.income_chf == 4200.00
    assert summary.expenses_chf == 1650.25
    assert summary.balance_chf == 2549.75
    assert summary.largest_expense_category == "Miete"


def test_integration_plan_transactions_and_report_work_together(budget_service, report_service):
    budget_service.save_plan(2030, 5, "4000", "2500", "500")
    transaction = budget_service.add_transaction("2030-05-04", "Ausgabe", "Lebensmittel", "95.90")
    budget_service.update_transaction(transaction.id, "2030-05-04", "Ausgabe", "Freizeit", "110.00", "Korrigiert")
    budget_service.add_transaction("2030-05-05", "Umbuchung", "Sparkonto", "200.00", "Notgroschen", "Budget zu Sparkonto")
    budget_service.add_transaction("2030-05-06", "Umbuchung", "Sparkonto", "50.00", "Zurück ins Monatsbudget", "Sparkonto zu Budget")

    summary = budget_service.monthly_summary(2030, 5)
    pdf_path = report_service.create_monthly_pdf(summary)
    csv_path = report_service.create_monthly_csv(summary)

    assert summary.plan is not None
    assert summary.plan.savings_goal_chf == 500.00
    assert summary.expenses_chf == 110.00
    assert summary.savings_booked_chf == 150.00
    assert summary.remaining_expense_budget_chf == 2240.00
    assert summary.savings_balance_chf >= 150.00
    assert summary.net_worth_chf == round(summary.budget_cash_chf + summary.savings_balance_chf, 2)
    assert summary.budget_health_score > 0
    assert summary.largest_expense_category == "Freizeit"
    assert pdf_path.exists()
    assert csv_path.exists()
    assert "Sparkonto" in csv_path.read_text(encoding="utf-8")
