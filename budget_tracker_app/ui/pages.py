"""NiceGUI page definitions."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ..services.budget_service import TRANSACTION_KINDS
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
            body { background: #f7f7f4; }
            .app-page { max-width: 1180px; margin: 0 auto; padding: 28px 18px 42px; }
            .metric { background: white; border: 1px solid #deded8; border-radius: 8px; padding: 14px 16px; min-height: 86px; }
            .muted { color: #62615d; }
            .amount-positive { color: #127a4a; font-weight: 700; }
            .amount-negative { color: #a33a2b; font-weight: 700; }
            .page-title { font-size: 2.4rem; font-weight: 600; margin-bottom: 4px; }
            .metrics-grid { display: grid; grid-template-columns: repeat(4, minmax(150px, 1fr)); gap: 12px; }
            .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 34px; align-items: start; }
            @media (max-width: 850px) {
                .metrics-grid { grid-template-columns: repeat(2, minmax(140px, 1fr)); }
                .form-grid { grid-template-columns: 1fr; }
            }
            </style>
            """
        )
        with ui.row().classes("w-full items-center justify-between"):
            ui.label(title).classes("page-title")
            with ui.row().classes("items-center gap-2"):
                ui.link("Budget", "/")
                ui.link("Kategorien", "/categories")
                ui.link("Einstellungen", "/settings")
                ui.button("Logout", on_click=lambda: (self.auth.logout(), ui.navigate.to("/login"))).props("flat")

    def _register_login(self) -> None:
        @ui.page("/login")
        def login_page() -> None:
            ui.add_head_html("<style>body { background: #f7f7f4; }</style>")
            with ui.column().classes("app-page w-full max-w-md mx-auto gap-4"):
                ui.markdown("# Budget Tracker")
                if not self.auth.has_account():
                    ui.label("Beim ersten Start ein Passwort festlegen.").classes("muted")
                    password = ui.input("Neues Passwort", password=True, password_toggle_button=True).classes("w-full")

                    def setup() -> None:
                        try:
                            self.auth.setup_password(password.value or "")
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                            return
                        ui.notify("Passwort gespeichert.", type="positive")
                        ui.navigate.to("/")

                    ui.button("Passwort speichern", on_click=setup).props("color=primary")
                    return

                password = ui.input("Passwort", password=True, password_toggle_button=True).classes("w-full")

                def login() -> None:
                    if self.auth.login(password.value or ""):
                        ui.navigate.to("/")
                    else:
                        ui.notify("Falsches Passwort.", type="negative")

                password.on("keydown.enter", login)
                ui.button("Einloggen", on_click=login).props("color=primary")

    def _register_dashboard(self) -> None:
        @ui.page("/")
        def dashboard_page() -> None:
            if not self._guard():
                return

            today = date.today()
            selected_month = {"year": today.year, "month": today.month}

            with ui.column().classes("app-page w-full gap-6"):
                self._shell("Budget Tracker")

                with ui.row().classes("w-full items-end gap-4"):
                    year_input = ui.number("Jahr", value=selected_month["year"], min=2000, max=2100, step=1).classes("w-32")
                    month_input = ui.number("Monat", value=selected_month["month"], min=1, max=12, step=1).classes("w-32")
                    ui.button("Monat anzeigen", on_click=lambda: refresh()).props("outline")

                summary_container = ui.column().classes("w-full")
                table_container = ui.column().classes("w-full")

                def month_values() -> tuple[int, int]:
                    return int(year_input.value or today.year), int(month_input.value or today.month)

                def refresh() -> None:
                    year, month = month_values()
                    selected_month.update({"year": year, "month": month})
                    summary = self.budget.summary(year, month)

                    summary_container.clear()
                    with summary_container:
                        with ui.element("div").classes("metrics-grid w-full"):
                            self._metric("Einnahmen", f"CHF {summary.income_chf:.2f}", "amount-positive")
                            self._metric("Ausgaben", f"CHF {summary.expenses_chf:.2f}", "amount-negative")
                            self._metric("Verfügbar", f"CHF {summary.balance_chf:.2f}", "amount-positive" if summary.balance_chf >= 0 else "amount-negative")
                            largest = summary.largest_expense_category or "Keine Ausgaben"
                            self._metric("Grösste Kategorie", f"{largest}", "muted")

                        with ui.element("div").classes("form-grid w-full"):
                            with ui.column().classes("w-full"):
                                ui.markdown("## Neue Buchung")
                                booking_date = ui.input("Datum", value=date.today().isoformat()).props("type=date").classes("w-full")
                                kind = ui.select(list(TRANSACTION_KINDS), value="Ausgabe", label="Typ").classes("w-full")
                                category = ui.select(self.budget.categories(), label="Kategorie", value=(self.budget.categories()[0] if self.budget.categories() else None)).classes("w-full")
                                amount = ui.input("Betrag CHF", value="0.00").classes("w-full")
                                note = ui.input("Notiz", value="").classes("w-full")

                                def save_transaction() -> None:
                                    try:
                                        self.budget.add_transaction(booking_date.value, kind.value, category.value, amount.value, note.value or "")
                                    except ValueError as exc:
                                        ui.notify(str(exc), type="warning")
                                        return
                                    ui.notify("Buchung gespeichert.", type="positive")
                                    refresh()

                                ui.button("Speichern", on_click=save_transaction).props("color=primary")

                            with ui.column().classes("w-full"):
                                ui.markdown("## Budgetplan")
                                plan = summary.plan
                                planned_income = ui.input("Geplante Einnahmen", value=f"{plan.planned_income_chf:.2f}" if plan else "0.00").classes("w-full")
                                planned_expenses = ui.input("Geplante Ausgaben", value=f"{plan.planned_expenses_chf:.2f}" if plan else "0.00").classes("w-full")
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

                                with ui.row().classes("gap-2"):
                                    ui.button("Plan speichern", on_click=save_plan).props("color=primary")
                                    ui.button("PDF exportieren", on_click=export_pdf).props("outline")

                    table_container.clear()
                    with table_container:
                        ui.markdown("## Monatliche Einträge")
                        rows = []
                        for transaction in summary.transactions:
                            rows.append(
                                {
                                    "id": transaction.id,
                                    "date": transaction.booking_date.strftime("%d.%m.%Y"),
                                    "kind": transaction.kind,
                                    "category": transaction.category.name if transaction.category else "Unbekannt",
                                    "note": transaction.note,
                                    "amount": f"{transaction.signed_amount_chf:.2f}",
                                }
                            )

                        columns = [
                            {"name": "date", "label": "Datum", "field": "date", "align": "left"},
                            {"name": "kind", "label": "Typ", "field": "kind", "align": "left"},
                            {"name": "category", "label": "Kategorie", "field": "category", "align": "left"},
                            {"name": "note", "label": "Notiz", "field": "note", "align": "left"},
                            {"name": "amount", "label": "Betrag CHF", "field": "amount", "align": "right"},
                            {"name": "actions", "label": "", "field": "actions", "align": "center"},
                        ]
                        table = ui.table(columns=columns, rows=rows, row_key="id").classes("w-full")
                        table.add_slot(
                            "body-cell-actions",
                            """
                            <q-td :props="props">
                                <q-btn dense outline color="negative" icon="delete" @click="$parent.$emit('delete_row', props.row.id)" />
                            </q-td>
                            """,
                        )
                        table.on("delete_row", lambda e: (self.budget.delete_transaction(int(e.args)), refresh()))

                refresh()

    def _register_categories(self) -> None:
        @ui.page("/categories")
        def categories_page() -> None:
            if not self._guard():
                return
            with ui.column().classes("app-page w-full gap-5"):
                self._shell("Kategorien")
                ui.markdown("## Kategorien verwalten")
                name = ui.input("Neue Kategorie").classes("w-full max-w-md")
                list_container = ui.column().classes("w-full")

                def refresh_list() -> None:
                    list_container.clear()
                    with list_container:
                        rows = [{"name": category} for category in self.categories.list_categories()]
                        ui.table(
                            columns=[{"name": "name", "label": "Kategorie", "field": "name", "align": "left"}],
                            rows=rows,
                        ).classes("w-full max-w-xl")

                def add() -> None:
                    try:
                        created = self.categories.add_category(name.value or "")
                    except ValueError as exc:
                        ui.notify(str(exc), type="warning")
                        return
                    name.value = ""
                    ui.notify(f"Kategorie {created} hinzugefügt.", type="positive")
                    refresh_list()

                ui.button("Kategorie hinzufügen", on_click=add).props("color=primary")
                refresh_list()

    def _register_settings(self) -> None:
        @ui.page("/settings")
        def settings_page() -> None:
            if not self._guard():
                return
            with ui.column().classes("app-page w-full gap-5"):
                self._shell("Einstellungen")
                ui.markdown("## Passwort ändern")
                current = ui.input("Aktuelles Passwort", password=True, password_toggle_button=True).classes("w-full max-w-md")
                new = ui.input("Neues Passwort", password=True, password_toggle_button=True).classes("w-full max-w-md")

                def change() -> None:
                    try:
                        self.auth.change_password(current.value or "", new.value or "")
                    except ValueError as exc:
                        ui.notify(str(exc), type="warning")
                        return
                    current.value = ""
                    new.value = ""
                    ui.notify("Passwort geändert.", type="positive")

                ui.button("Passwort speichern", on_click=change).props("color=primary")

    @staticmethod
    def _metric(label: str, value: str, value_class: str) -> None:
        with ui.column().classes("metric"):
            ui.label(label).classes("muted")
            ui.label(value).classes(f"text-xl {value_class}")
