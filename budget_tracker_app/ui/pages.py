"""NiceGUI page definitions."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ..services.budget_service import (
    SAVINGS_CATEGORY,
    TRANSACTION_KINDS,
    TRANSFER_DIRECTIONS,
    TRANSFER_DIRECTION_ALIASES,
)
from .controllers import AuthController, BudgetController, CategoryController


class Pages:
    """Registers all browser routes."""

    def __init__(
        self,
        auth_controller: AuthController,
        budget_controller: BudgetController,
        category_controller: CategoryController,
    ) -> None:
        self.auth = auth_controller
        self.budget = budget_controller
        self.categories = category_controller

    def register(self) -> None:
        self._register_login()
        self._register_dashboard()
        self._register_categories()
        self._register_settings()

    def _guard(self) -> bool:
        if not self.auth.is_authenticated():
            ui.navigate.to("/login")
            return False
        return True

    def _shell(self, title: str) -> None:
        ui.add_head_html(
            """
            <style>
            :root {
                --app-bg: #f4f7f3;
                --surface: #ffffff;
                --surface-soft: #f8fbf6;
                --ink: #15202b;
                --muted: #64748b;
                --line: #d7e3d8;
                --brand: #0f766e;
                --brand-strong: #134e4a;
                --green: #059669;
                --red: #b91c1c;
                --amber: #b45309;
                --blue: #1d4ed8;
                --violet: #6d28d9;
            }
            body {
                background:
                    radial-gradient(circle at top left, rgba(16, 185, 129, 0.16), transparent 30%),
                    linear-gradient(180deg, rgba(15, 118, 110, 0.08), rgba(5, 150, 105, 0.04) 36%, rgba(180, 83, 9, 0.04) 100%),
                    var(--app-bg);
                color: var(--ink);
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            .app-shell .q-field__control {
                border-radius: 8px;
                background: #ffffff;
                border: 1px solid rgba(15, 118, 110, 0.08);
            }
            .app-shell .q-btn {
                border-radius: 8px;
                font-weight: 700;
                letter-spacing: 0;
                transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease;
            }
            .app-shell .q-btn:hover {
                transform: translateY(-1px);
            }
            .app-shell .q-table__container {
                border-radius: 8px;
                box-shadow: none;
            }
            .app-shell .q-table th {
                color: #475569;
                font-size: 0.75rem;
                font-weight: 800;
                letter-spacing: 0;
                text-transform: uppercase;
                background: #f8fafc;
            }
            .app-shell .q-table td {
                color: #1f2937;
                font-size: 0.875rem;
            }
            .transaction-table tbody tr {
                transition: background 150ms ease;
            }
            .transaction-table tbody tr:hover {
                background: #ecfdf5;
            }
            .app-panel {
                background: var(--surface);
                border: 1px solid var(--line);
                border-top: 4px solid rgba(5, 150, 105, 0.88);
                border-radius: 8px;
                box-shadow: 0 14px 36px rgba(20, 83, 45, 0.08);
                transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
            }
            .app-panel:hover {
                transform: translateY(-1px);
                box-shadow: 0 18px 44px rgba(20, 83, 45, 0.11);
                border-color: #a7f3d0;
            }
            .app-header {
                background: linear-gradient(135deg, #064e3b 0%, #0f766e 65%, #059669 100%);
                border: 0;
                border-radius: 8px;
                box-shadow: 0 16px 38px rgba(6, 78, 59, 0.22);
            }
            .app-header .q-btn {
                color: white;
            }
            .app-soft-panel {
                background: linear-gradient(135deg, #ffffff 0%, #f0fdf4 100%);
                border: 1px solid #bbf7d0;
                border-radius: 8px;
            }
            .metric-accent {
                width: 36px;
                height: 4px;
                border-radius: 999px;
            }
            .metric-card {
                background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
                border: 1px solid #d7e3d8;
                border-radius: 8px;
                box-shadow: 0 10px 26px rgba(20, 83, 45, 0.07);
                transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
            }
            .metric-card:hover {
                transform: translateY(-1px);
                border-color: #86efac;
                box-shadow: 0 16px 34px rgba(20, 83, 45, 0.11);
            }
            .progress-track {
                width: 100%;
                height: 10px;
                background: #e6ebe4;
                border-radius: 999px;
                overflow: hidden;
            }
            .progress-fill {
                height: 100%;
                border-radius: 999px;
            }
            .tip-list {
                margin: 0;
                padding-left: 18px;
                color: var(--muted);
            }
            .transaction-table .q-table__top,
            .transaction-table .q-table__bottom {
                background: white;
            }
            .edit-dialog {
                width: min(560px, 92vw);
                border-radius: 8px;
            }
            @media (max-width: 767px) {
                .app-nav {
                    width: 100%;
                    justify-content: flex-start;
                    overflow-x: auto;
                    padding-bottom: 2px;
                }
            }
            </style>
            """
        )
        with ui.row().classes("w-full items-center justify-between gap-4 app-header px-4 py-4 md:px-5"):
            with ui.row().classes("items-center gap-3"):
                ui.icon("account_balance_wallet").classes("text-white text-3xl")
                with ui.column().classes("gap-0"):
                    ui.label(title).classes("text-2xl font-bold leading-tight text-white")
                    ui.label("Persönlicher Budget Tracker").classes("text-sm text-emerald-100")
            with ui.row().classes("app-nav items-center gap-1"):
                self._nav_link("Übersicht", "/", "dashboard")
                self._nav_link("Kategorien", "/categories", "sell")
                self._nav_link("Einstellungen", "/settings", "settings")
                ui.button("Logout", icon="logout", on_click=lambda: (self.auth.logout(), ui.navigate.to("/login"))).props(
                    "unelevated color=negative"
                )

    def _register_login(self) -> None:
        @ui.page("/login")
        def login_page() -> None:
            ui.add_head_html(
                """
                <style>
                body {
                    background:
                        radial-gradient(circle at top left, rgba(16, 185, 129, 0.18), transparent 32%),
                        linear-gradient(135deg, #f0fdf4 0%, #f8fafc 52%, #ecfdf5 100%);
                    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                }
                .app-panel {
                    background: #ffffff;
                    border: 1px solid #bbf7d0;
                    border-top: 4px solid #059669;
                    border-radius: 8px;
                    box-shadow: 0 24px 64px rgba(6, 78, 59, 0.14);
                }
                .login-card .q-btn, .login-card .q-field__control { border-radius: 8px; }
                </style>
                """
            )
            with ui.element("div").classes("min-h-screen flex items-center justify-center px-5 py-8"):
                with ui.column().classes("login-card w-full max-w-md app-panel p-8 gap-5"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("account_balance_wallet").classes("text-emerald-700 text-4xl")
                        with ui.column().classes("gap-0"):
                            ui.label("Budget Tracker").classes("text-3xl font-bold leading-tight text-slate-950")
                            ui.label("Lokale Finanzübersicht").classes("text-sm text-emerald-700")

                    if not self.auth.has_account():
                        ui.label("Lege beim ersten Start dein Passwort fest.").classes("text-slate-600")
                        password = ui.input("Neues Passwort", password=True, password_toggle_button=True).classes("w-full")

                        def setup() -> None:
                            try:
                                self.auth.setup_password(password.value or "")
                            except ValueError as exc:
                                ui.notify(str(exc), type="warning")
                                return
                            ui.notify("Passwort gespeichert.", type="positive")
                            ui.navigate.to("/")

                        ui.button("Passwort speichern", icon="save", on_click=setup).props("color=positive unelevated").classes("w-full py-3")
                        return

                    password = ui.input("Passwort", password=True, password_toggle_button=True).classes("w-full")

                    def login() -> None:
                        if self.auth.login(password.value or ""):
                            ui.navigate.to("/")
                        else:
                            ui.notify("Falsches Passwort.", type="negative")

                    password.on("keydown.enter", login)
                    ui.button("Einloggen", icon="login", on_click=login).props("color=positive unelevated").classes("w-full py-3")

    def _register_dashboard(self) -> None:
        @ui.page("/")
        def dashboard_page() -> None:
            if not self._guard():
                return

            today = date.today()
            selected_month = {"year": today.year, "month": today.month}

            with ui.column().classes("app-shell w-full max-w-7xl mx-auto px-4 py-6 gap-5"):
                self._shell("Übersicht")

                with ui.row().classes("w-full items-end justify-between gap-3 app-soft-panel px-4 py-4 shadow-sm"):
                    with ui.row().classes("items-end gap-3"):
                        year_input = ui.number("Jahr", value=selected_month["year"], min=2000, max=2100, step=1).classes("w-32")
                        month_input = ui.number("Monat", value=selected_month["month"], min=1, max=12, step=1).classes("w-32")
                    ui.button("Monat anzeigen", icon="calendar_month", on_click=lambda: refresh()).props(
                        "outline color=primary"
                    )

                summary_container = ui.column().classes("w-full gap-4")
                table_container = ui.column().classes("w-full")

                def month_values() -> tuple[int, int]:
                    return int(year_input.value or today.year), int(month_input.value or today.month)

                def refresh() -> None:
                    year, month = month_values()
                    selected_month.update({"year": year, "month": month})
                    summary = self.budget.summary(year, month)
                    previous_year, previous_month = self._previous_month(year, month)
                    previous_summary = self.budget.summary(previous_year, previous_month)
                    categories = self.budget.categories()
                    default_category = "Lebensmittel" if "Lebensmittel" in categories else (categories[0] if categories else None)

                    summary_container.clear()
                    with summary_container:
                        largest_label = summary.largest_expense_category or "Keine Ausgaben"
                        largest_subtitle = (
                            f"CHF {summary.largest_expense_chf:.2f} - {summary.largest_expense_share_pct:.1f}% der Ausgaben"
                            if summary.largest_expense_category
                            else "Noch keine Kategorie belastet"
                        )
                        free_to_spend = summary.remaining_expense_budget_chf if summary.plan else summary.balance_chf
                        free_class = "text-emerald-700" if free_to_spend >= 0 else "text-red-700"
                        free_subtitle = "Restbudget" if summary.plan else "Saldo ohne Monatsplan"
                        expense_delta = round(summary.expenses_chf - previous_summary.expenses_chf, 2)
                        delta_class = "text-emerald-700" if expense_delta <= 0 else "text-red-700"
                        delta_sign = "+" if expense_delta > 0 else ""
                        health_class = "text-emerald-700" if summary.budget_health_score >= 80 else "text-amber-700"
                        if summary.budget_health_score < 60:
                            health_class = "text-red-700"
                        day_class = "text-emerald-700" if summary.available_per_day_chf >= 0 else "text-red-700"

                        with ui.element("div").classes("w-full grid grid-cols-1 xl:grid-cols-3 gap-4"):
                            with ui.column().classes("app-panel p-5 gap-4 xl:col-span-2"):
                                with ui.row().classes("w-full items-start justify-between gap-3"):
                                    with ui.column().classes("gap-1"):
                                        ui.label(f"{month:02d}.{year}").classes("text-sm font-bold uppercase text-emerald-700")
                                        ui.label("Monatsstatus").classes("text-3xl font-bold leading-tight text-slate-950")
                                    ui.badge(summary.budget_health_label).props(self._badge_props(summary.budget_health_score)).classes("px-3 py-2")
                                with ui.element("div").classes("w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3"):
                                    self._metric("Einnahmen", self._chf(summary.income_chf), "text-emerald-700", "Gebucht im Monat", "bg-emerald-600")
                                    self._metric("Ausgaben", self._chf(summary.expenses_chf), "text-red-700", "Gebucht im Monat", "bg-red-600")
                                    self._metric("Noch frei", self._chf(free_to_spend), free_class, free_subtitle, "bg-cyan-700")
                                    self._metric("Pro Tag frei", self._chf(summary.available_per_day_chf), day_class, "Bis Monatsende", "bg-amber-600")
                            with ui.column().classes("app-panel p-5 gap-4"):
                                self._section_title("Konten", "account_balance")
                                self._mini_fact("Budgetkonto", summary.budget_cash_chf, "account_balance")
                                self._mini_fact("Sparkonto", summary.savings_balance_chf, "savings")
                                self._mini_fact("Nettovermögen", summary.net_worth_chf, "monitoring")

                        with ui.element("div").classes("w-full grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3"):
                            self._metric("Grösste Kategorie", largest_label, "text-blue-700", largest_subtitle, "bg-blue-600")
                            self._metric("Monatsvergleich", f"{delta_sign}{self._chf(expense_delta)}", delta_class, "Ausgaben vs. Vormonat", "bg-violet-600")
                            self._metric("Netto gespart", self._chf(summary.savings_booked_chf), "text-blue-700", "Umbuchungen Sparkonto", "bg-cyan-700")
                            self._metric("Budget-Health", f"{summary.budget_health_score}/100", health_class, summary.budget_health_label, "bg-emerald-600")
                            self._metric("Cashflow", self._chf(summary.cash_flow_chf), self._amount_class(summary.cash_flow_chf), "Einnahmen minus Ausgaben", "bg-slate-700")

                        if summary.plan and summary.spending_budget_used_pct >= 100:
                            self._warning(
                                "Budget-Limite überschritten",
                                "Du hast mehr Budget genutzt als geplant. Prüfe die grössten Kategorien und verschiebe falls nötig Geld vom Sparkonto zurück.",
                            )
                        elif summary.plan and summary.spending_budget_used_pct >= 80:
                            self._warning(
                                "Budget-Limite bald erreicht",
                                "Du hast bereits über 80% deines Monatsbudgets genutzt.",
                            )

                        with ui.element("div").classes("w-full grid grid-cols-1 lg:grid-cols-2 gap-4"):
                            with ui.column().classes("app-panel p-5 gap-3"):
                                self._section_title("Ausgaben-Verteilung", "donut_large")
                                self._pie_chart(summary.category_expenses)
                            with ui.column().classes("app-panel p-5 gap-3"):
                                self._section_title("Monatsvergleich", "bar_chart")
                                self._comparison_chart(summary, previous_summary)

                        with ui.column().classes("w-full gap-4"):
                            with ui.column().classes("app-panel p-5 gap-4 w-full"):
                                self._section_title("Neue Buchung", "add_card")
                                with ui.element("div").classes("w-full grid grid-cols-1 md:grid-cols-2 gap-3"):
                                    booking_date = ui.input("Datum", value=date.today().isoformat()).props("type=date").classes("w-full")
                                    kind = ui.select(list(TRANSACTION_KINDS), value="Ausgabe", label="Typ").classes("w-full")
                                transfer_direction = ui.select(
                                    list(TRANSFER_DIRECTIONS),
                                    value=TRANSFER_DIRECTIONS[0],
                                    label="Richtung",
                                ).classes("w-full")
                                category = ui.select(categories, label="Kategorie", value=default_category).classes("w-full")
                                with ui.row().classes("w-full items-end gap-2") as category_create_row:
                                    new_category = ui.input("Neue Kategorie").classes("flex-1")

                                    def add_inline_category() -> None:
                                        try:
                                            created = self.budget.add_category(new_category.value or "")
                                        except ValueError as exc:
                                            ui.notify(str(exc), type="warning")
                                            return
                                        updated_categories = self.budget.categories()
                                        category.options = updated_categories
                                        category.value = created
                                        category.update()
                                        new_category.value = ""
                                        new_category.update()
                                        ui.notify(f"Kategorie {created} hinzugefügt.", type="positive")

                                    ui.button(icon="add", on_click=add_inline_category).props("round outline color=primary").tooltip(
                                        "Kategorie hinzufügen"
                                    )

                                def update_kind_controls() -> None:
                                    is_transfer = kind.value == "Umbuchung"
                                    transfer_direction.visible = is_transfer
                                    category.visible = not is_transfer
                                    category_create_row.visible = not is_transfer
                                    if is_transfer and SAVINGS_CATEGORY in categories:
                                        category.value = SAVINGS_CATEGORY
                                    transfer_direction.update()
                                    category.update()
                                    category_create_row.update()

                                kind.on_value_change(lambda _: update_kind_controls())
                                update_kind_controls()

                                with ui.element("div").classes("w-full grid grid-cols-1 md:grid-cols-2 gap-3"):
                                    amount = ui.input("Betrag CHF", value="0.00").classes("w-full")
                                    note = ui.input("Notiz", value="").classes("w-full")

                                def save_transaction() -> None:
                                    try:
                                        self.budget.add_transaction(
                                            booking_date.value,
                                            kind.value,
                                            category.value,
                                            amount.value,
                                            note.value or "",
                                            transfer_direction.value if kind.value == "Umbuchung" else None,
                                        )
                                    except ValueError as exc:
                                        ui.notify(str(exc), type="warning")
                                        return
                                    ui.notify("Buchung gespeichert.", type="positive")
                                    refresh()

                                ui.button("Buchung speichern", icon="save", on_click=save_transaction).props(
                                    "color=positive unelevated"
                                ).classes("self-start px-5 py-2")

                            with ui.column().classes("app-panel p-5 gap-4 w-full"):
                                self._section_title("Monatsplan", "event_note")
                                plan = summary.plan
                                with ui.element("div").classes("w-full grid grid-cols-1 md:grid-cols-3 gap-3"):
                                    planned_income = ui.input(
                                        "Geplante Einnahmen",
                                        value=f"{plan.planned_income_chf:.2f}" if plan else "0.00",
                                    ).classes("w-full")
                                    planned_expenses = ui.input(
                                        "Geplante Ausgaben",
                                        value=f"{plan.planned_expenses_chf:.2f}" if plan else "0.00",
                                    ).classes("w-full")
                                    savings_goal = ui.input("Sparziel", value=f"{plan.savings_goal_chf:.2f}" if plan else "0.00").classes("w-full")

                                def save_plan() -> None:
                                    try:
                                        self.budget.save_plan(year, month, planned_income.value, planned_expenses.value, savings_goal.value)
                                    except ValueError as exc:
                                        ui.notify(str(exc), type="warning")
                                        return
                                    ui.notify("Budgetplan gespeichert.", type="positive")
                                    refresh()

                                def export_pdf() -> None:
                                    path = self.budget.export_pdf(year, month)
                                    ui.notify(f"PDF gespeichert: {path}", type="positive")

                                def export_csv() -> None:
                                    path = self.budget.export_csv(year, month)
                                    ui.notify(f"CSV gespeichert: {path}", type="positive")

                                with ui.row().classes("gap-2 flex-wrap"):
                                    ui.button("Plan speichern", icon="save", on_click=save_plan).props("color=positive unelevated")
                                    ui.button("PDF", icon="picture_as_pdf", on_click=export_pdf).props("outline color=primary")
                                    ui.button("CSV", icon="table_view", on_click=export_csv).props("outline color=primary")

                                if summary.plan:
                                    budget_tone = "bg-red-600" if summary.spending_budget_used_pct > 100 else "bg-emerald-700"
                                    self._progress(
                                        "Budget genutzt",
                                        summary.spending_budget_used_pct,
                                        f"Ausgaben und Umbuchungen {self._chf(summary.budget_used_chf)} von {self._chf(summary.planned_expenses_chf)}",
                                        budget_tone,
                                    )
                                    savings_detail = (
                                        f"Netto gespart {self._chf(summary.savings_booked_chf)} bei Ziel {self._chf(summary.plan.savings_goal_chf)}"
                                        if summary.savings_booked_chf >= 0
                                        else f"Vom Sparkonto geholt {self._chf(abs(summary.savings_booked_chf))} bei Ziel {self._chf(summary.plan.savings_goal_chf)}"
                                    )
                                    self._progress(
                                        "Sparziel erreicht",
                                        summary.savings_goal_progress_pct,
                                        savings_detail,
                                        "bg-blue-600",
                                    )

                                ui.separator()
                                self._section_title("Ausgaben nach Kategorie", "category")
                                top_categories = sorted(summary.category_expenses.items(), key=lambda item: item[1], reverse=True)[:5]
                                if not top_categories:
                                    ui.label("Noch keine Ausgaben in diesem Monat.").classes("text-slate-500")
                                for category_name, spent in top_categories:
                                    share = round((spent / summary.expenses_chf) * 100, 1) if summary.expenses_chf else 0.0
                                    self._category_bar(category_name, spent, share)

                                ui.separator()
                                self._section_title("Wiederkehrende Ausgaben", "autorenew")
                                if not summary.recurring_expenses:
                                    ui.label("Noch nicht genug Historie für sichere Erkennung.").classes("text-slate-500")
                                for recurring in summary.recurring_expenses:
                                    ui.label(
                                        f"{recurring.name}: {self._chf(recurring.monthly_amount_chf)}/Monat "
                                        f"(ca. {self._chf(recurring.yearly_amount_chf)}/Jahr)"
                                    ).classes("text-slate-600")

                                ui.separator()
                                self._section_title("Spartipps", "lightbulb")
                                with ui.element("ul").classes("tip-list"):
                                    for tip in self._spending_tips(summary, previous_summary):
                                        with ui.element("li").classes("mb-1"):
                                            ui.label(tip)

                    table_container.clear()
                    with table_container:
                        with ui.column().classes("app-panel p-5 w-full gap-3"):
                            self._section_title("Monatliche Buchungen", "receipt_long")
                            all_rows = [
                                {
                                    "id": transaction.id,
                                    "date": transaction.booking_date.strftime("%d.%m.%Y"),
                                    "raw_date": transaction.booking_date.isoformat(),
                                    "kind": transaction.kind,
                                    "direction": TRANSFER_DIRECTION_ALIASES.get(transaction.transfer_direction, transaction.transfer_direction or ""),
                                    "category": (
                                        "Sparkonto"
                                        if transaction.kind == "Umbuchung"
                                        else (transaction.category.name if transaction.category else "Unbekannt")
                                    ),
                                    "note": transaction.note,
                                    "amount": f"{transaction.signed_amount_chf:.2f}",
                                }
                                for transaction in summary.transactions
                            ]
                            columns = [
                                {"name": "date", "label": "Datum", "field": "date", "align": "left"},
                                {"name": "kind", "label": "Typ", "field": "kind", "align": "left"},
                                {"name": "direction", "label": "Richtung", "field": "direction", "align": "left"},
                                {"name": "category", "label": "Kategorie", "field": "category", "align": "left"},
                                {"name": "note", "label": "Notiz", "field": "note", "align": "left"},
                                {"name": "amount", "label": "Betrag CHF", "field": "amount", "align": "right"},
                                {"name": "actions", "label": "", "field": "actions", "align": "center"},
                            ]
                            with ui.element("div").classes("w-full grid grid-cols-1 md:grid-cols-3 gap-3"):
                                search_input = ui.input("Suche", placeholder="Notiz, Kategorie, Typ").props("clearable").classes("w-full")
                                kind_filter = ui.select(["Alle", *TRANSACTION_KINDS], value="Alle", label="Typ filtern").classes("w-full")
                                category_options = ["Alle", *sorted({row["category"] for row in all_rows})]
                                category_filter = ui.select(category_options, value="Alle", label="Kategorie filtern").classes("w-full")
                            filtered_table = ui.column().classes("w-full")

                            def render_filtered_table() -> None:
                                search_term = (search_input.value or "").strip().lower()
                                filtered_rows = []
                                for row in all_rows:
                                    haystack = " ".join(str(row[key]) for key in ("kind", "direction", "category", "note", "amount")).lower()
                                    if search_term and search_term not in haystack:
                                        continue
                                    if kind_filter.value != "Alle" and row["kind"] != kind_filter.value:
                                        continue
                                    if category_filter.value != "Alle" and row["category"] != category_filter.value:
                                        continue
                                    filtered_rows.append(row)

                                filtered_table.clear()
                                with filtered_table:
                                    ui.label(f"{len(filtered_rows)} von {len(all_rows)} Buchungen").classes("text-slate-500")
                                    table = ui.table(columns=columns, rows=filtered_rows, row_key="id").classes(
                                        "transaction-table w-full min-h-72"
                                    )
                                    table.props("flat bordered :rows-per-page-options='[10, 20, 50]'")
                                    table.add_slot(
                                        "body-cell-actions",
                                        """
                                        <q-td :props="props">
                                            <q-btn dense flat round color="primary" icon="edit" @click="$parent.$emit('edit_row', props.row.id)" />
                                            <q-btn dense flat round color="negative" icon="delete" @click="$parent.$emit('delete_row', props.row.id)" />
                                        </q-td>
                                        """,
                                    )
                                    table.on("edit_row", lambda e: open_edit_dialog(int(e.args)))
                                    table.on("delete_row", lambda e: (self.budget.delete_transaction(int(e.args)), refresh()))

                            search_input.on_value_change(lambda _: render_filtered_table())
                            kind_filter.on_value_change(lambda _: render_filtered_table())
                            category_filter.on_value_change(lambda _: render_filtered_table())
                            render_filtered_table()

                def open_edit_dialog(transaction_id: int) -> None:
                    transaction = self.budget.transaction(transaction_id)
                    if transaction is None:
                        ui.notify("Buchung nicht gefunden.", type="warning")
                        return

                    categories = self.budget.categories()
                    current_category = transaction.category.name if transaction.category else (categories[0] if categories else None)
                    dialog = ui.dialog()
                    with dialog, ui.card().classes("edit-dialog gap-4"):
                        self._section_title("Buchung bearbeiten", "edit")
                        edit_date = ui.input("Datum", value=transaction.booking_date.isoformat()).props("type=date").classes("w-full")
                        edit_kind = ui.select(list(TRANSACTION_KINDS), value=transaction.kind, label="Typ").classes("w-full")
                        edit_transfer_direction = ui.select(
                            list(TRANSFER_DIRECTIONS),
                            value=TRANSFER_DIRECTION_ALIASES.get(transaction.transfer_direction, transaction.transfer_direction or TRANSFER_DIRECTIONS[0]),
                            label="Richtung",
                        ).classes("w-full")
                        edit_category = ui.select(categories, value=current_category, label="Kategorie").classes("w-full")
                        edit_amount = ui.input("Betrag CHF", value=f"{transaction.amount_chf:.2f}").classes("w-full")
                        edit_note = ui.input("Notiz", value=transaction.note).classes("w-full")

                        def update_edit_kind_controls() -> None:
                            is_transfer = edit_kind.value == "Umbuchung"
                            edit_transfer_direction.visible = is_transfer
                            edit_category.visible = not is_transfer
                            if is_transfer and SAVINGS_CATEGORY in categories:
                                edit_category.value = SAVINGS_CATEGORY
                            edit_transfer_direction.update()
                            edit_category.update()

                        edit_kind.on_value_change(lambda _: update_edit_kind_controls())
                        update_edit_kind_controls()

                        def save_edit() -> None:
                            try:
                                self.budget.update_transaction(
                                    transaction_id,
                                    edit_date.value,
                                    edit_kind.value,
                                    edit_category.value,
                                    edit_amount.value,
                                    edit_note.value or "",
                                    edit_transfer_direction.value if edit_kind.value == "Umbuchung" else None,
                                )
                            except ValueError as exc:
                                ui.notify(str(exc), type="warning")
                                return
                            dialog.close()
                            ui.notify("Buchung aktualisiert.", type="positive")
                            refresh()

                        with ui.row().classes("gap-2"):
                            ui.button("Speichern", icon="save", on_click=save_edit).props("color=primary unelevated")
                            ui.button("Abbrechen", icon="close", on_click=dialog.close).props("flat")
                    dialog.open()

                refresh()

    def _register_categories(self) -> None:
        @ui.page("/categories")
        def categories_page() -> None:
            if not self._guard():
                return
            with ui.column().classes("app-shell w-full max-w-7xl mx-auto px-4 py-6 gap-5"):
                self._shell("Kategorien")
                with ui.column().classes("app-panel p-5 gap-4"):
                    self._section_title("Kategorien verwalten", "sell")
                    with ui.row().classes("w-full max-w-2xl items-end gap-2"):
                        name = ui.input("Neue Kategorie").classes("flex-1")
                        ui.button(icon="add", on_click=lambda: add()).props("round color=primary").tooltip("Kategorie hinzufügen")
                    list_container = ui.column().classes("w-full")

                    def refresh_list() -> None:
                        list_container.clear()
                        with list_container:
                            rows = [{"name": category} for category in self.categories.list_categories()]
                            ui.table(
                                columns=[{"name": "name", "label": "Kategorie", "field": "name", "align": "left"}],
                                rows=rows,
                            ).classes("w-full max-w-2xl").props("flat bordered")

                    def add() -> None:
                        try:
                            created = self.categories.add_category(name.value or "")
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                            return
                        name.value = ""
                        ui.notify(f"Kategorie {created} hinzugefügt.", type="positive")
                        refresh_list()

                    refresh_list()

    def _register_settings(self) -> None:
        @ui.page("/settings")
        def settings_page() -> None:
            if not self._guard():
                return
            with ui.column().classes("app-shell w-full max-w-7xl mx-auto px-4 py-6 gap-5"):
                self._shell("Einstellungen")
                with ui.column().classes("app-panel p-5 gap-4 max-w-2xl"):
                    self._section_title("Passwort ändern", "lock_reset")
                    current = ui.input("Aktuelles Passwort", password=True, password_toggle_button=True).classes("w-full")
                    new = ui.input("Neues Passwort", password=True, password_toggle_button=True).classes("w-full")

                    def change() -> None:
                        try:
                            self.auth.change_password(current.value or "", new.value or "")
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                            return
                        current.value = ""
                        new.value = ""
                        ui.notify("Passwort geändert.", type="positive")

                    ui.button("Passwort speichern", icon="save", on_click=change).props("color=primary unelevated")

    @staticmethod
    def _previous_month(year: int, month: int) -> tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def _nav_link(label: str, target: str, icon: str) -> None:
        with ui.link(target=target).classes(
            "no-underline text-white hover:text-white bg-white/10 hover:bg-white/20 px-3 py-2 rounded-lg transition-all duration-200"
        ):
            with ui.row().classes("items-center gap-2 no-wrap"):
                ui.icon(icon).classes("text-base")
                ui.label(label).classes("font-bold text-sm")

    @staticmethod
    def _section_title(title: str, icon: str) -> None:
        with ui.row().classes("items-center gap-2 pb-1"):
            ui.icon(icon).classes("text-emerald-700 text-xl")
            ui.label(title).classes("text-xl font-bold leading-snug text-slate-950")

    @staticmethod
    def _warning(title: str, message: str) -> None:
        with ui.column().classes("bg-amber-50 border border-amber-200 rounded-lg p-5 gap-1"):
            with ui.row().classes("items-center gap-2"):
                ui.icon("warning").classes("text-amber-700")
                ui.label(title).classes("text-lg font-bold leading-snug text-amber-800")
            ui.label(message).classes("text-slate-600")

    @staticmethod
    def _pie_chart(category_expenses: dict[str, float]) -> None:
        data = [{"name": name, "value": value} for name, value in sorted(category_expenses.items(), key=lambda item: item[1], reverse=True)]
        if not data:
            ui.label("Noch keine Ausgaben für ein Diagramm.").classes("text-slate-500")
            return
        ui.echart(
            {
                "color": ["#0e7490", "#047857", "#b45309", "#be123c", "#6d28d9", "#475569", "#16a34a"],
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": 0, "left": "center", "textStyle": {"color": "#475569"}},
                "series": [
                    {
                        "type": "pie",
                        "radius": ["44%", "70%"],
                        "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                        "label": {"formatter": "{b}: {d}%", "color": "#334155"},
                        "data": data,
                    }
                ],
            }
        ).classes("w-full h-72")

    @staticmethod
    def _comparison_chart(summary, previous_summary) -> None:
        ui.echart(
            {
                "color": ["#b91c1c", "#0e7490", "#047857"],
                "tooltip": {"trigger": "axis"},
                "legend": {"top": 0, "textStyle": {"color": "#475569"}},
                "grid": {"top": 44, "left": 44, "right": 16, "bottom": 36},
                "xAxis": {"type": "category", "data": ["Vormonat", "Aktuell"], "axisLabel": {"color": "#475569"}},
                "yAxis": {"type": "value", "axisLabel": {"color": "#475569"}},
                "series": [
                    {
                        "name": "Ausgaben",
                        "type": "bar",
                        "data": [previous_summary.expenses_chf, summary.expenses_chf],
                    },
                    {
                        "name": "Budget genutzt",
                        "type": "bar",
                        "data": [previous_summary.budget_used_chf, summary.budget_used_chf],
                    },
                    {
                        "name": "Netto gespart",
                        "type": "bar",
                        "data": [previous_summary.savings_booked_chf, summary.savings_booked_chf],
                    },
                ],
            }
        ).classes("w-full h-72")

    @staticmethod
    def _spending_tips(summary, previous_summary) -> list[str]:
        tips: list[str] = []
        if summary.budget_health_score < 60:
            tips.append(f"Budget-Health ist {summary.budget_health_label}: Plan, Ausgaben und Sparziel kurz prüfen.")

        if summary.plan and summary.available_per_day_chf > 0:
            tips.append(f"Bis Monatsende sind ungefähr CHF {summary.available_per_day_chf:.2f} pro Tag frei.")

        if summary.plan and summary.spending_budget_used_pct >= 100:
            tips.append("Budget-Limite ist überschritten: zuerst grosse Kategorien prüfen, bevor neue Ausgaben dazukommen.")
        elif summary.plan and summary.spending_budget_used_pct >= 80:
            tips.append("Budget-Limite ist bald erreicht: kleine Alltagsausgaben diese Woche bewusster planen.")

        if summary.largest_expense_category and summary.largest_expense_share_pct >= 40:
            tips.append(f"{summary.largest_expense_category} macht {summary.largest_expense_share_pct:.1f}% der Ausgaben aus.")

        if summary.expenses_chf > previous_summary.expenses_chf and previous_summary.expenses_chf > 0:
            delta = summary.expenses_chf - previous_summary.expenses_chf
            tips.append(f"Ausgaben sind CHF {delta:.2f} höher als im Vormonat.")

        if summary.plan and summary.savings_goal_progress_pct < 50:
            tips.append("Sparziel ist noch unter 50%: prüfe, ob eine kleine Umbuchung aufs Sparkonto möglich ist.")

        return tips or ["Dieser Monat sieht stabil aus. Budget und Sparkonto weiter beobachten."]

    @staticmethod
    def _metric(label: str, value: str, value_class: str, subtitle: str = "", accent_class: str = "bg-cyan-700") -> None:
        with ui.column().classes("metric-card p-4 min-h-32 gap-2"):
            ui.element("div").classes(f"metric-accent {accent_class}")
            ui.label(label).classes("text-slate-500 text-xs font-bold uppercase")
            ui.label(value).classes(f"text-2xl font-bold leading-tight break-words {value_class}")
            if subtitle:
                ui.label(subtitle).classes("text-slate-500 text-sm leading-tight")

    @staticmethod
    def _progress(label: str, percent: float, detail: str, tone: str) -> None:
        safe_percent = max(0.0, min(percent, 100.0))
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("w-full items-center justify-between gap-3"):
                ui.label(label).classes("font-bold text-slate-900")
                ui.label(f"{percent:.1f}%").classes("text-slate-500")
            with ui.element("div").classes("progress-track"):
                ui.element("div").classes(f"progress-fill {tone}").style(f"width: {safe_percent}%;")
            ui.label(detail).classes("text-slate-500 text-xs")

    @staticmethod
    def _mini_fact(label: str, amount: float, icon: str) -> None:
        amount_class = Pages._amount_class(amount)
        with ui.row().classes("w-full items-center justify-between gap-3 app-soft-panel px-3 py-2"):
            with ui.row().classes("items-center gap-2"):
                ui.icon(icon).classes("text-cyan-800")
                ui.label(label).classes("font-bold text-slate-700")
            ui.label(Pages._chf(amount)).classes(f"font-bold {amount_class}")

    @staticmethod
    def _category_bar(category_name: str, spent: float, share: float) -> None:
        safe_share = max(0.0, min(share, 100.0))
        with ui.column().classes("w-full gap-2"):
            with ui.row().classes("w-full items-center justify-between gap-2"):
                ui.label(category_name).classes("font-bold text-slate-900")
                ui.label(f"{Pages._chf(spent)} · {share:.1f}%").classes("text-slate-500")
            with ui.element("div").classes("progress-track"):
                ui.element("div").classes("progress-fill bg-amber-600").style(f"width: {safe_share}%;")

    @staticmethod
    def _badge_props(score: int) -> str:
        if score >= 80:
            return "color=green text-color=white"
        if score >= 60:
            return "color=amber text-color=white"
        return "color=red text-color=white"

    @staticmethod
    def _amount_class(amount: float) -> str:
        return "text-emerald-700" if amount >= 0 else "text-red-700"

    @staticmethod
    def _chf(amount: float) -> str:
        return f"CHF {amount:.2f}"
