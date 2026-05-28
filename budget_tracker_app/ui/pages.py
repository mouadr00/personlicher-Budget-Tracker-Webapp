"""NiceGUI page definitions."""

from __future__ import annotations

from datetime import date

from nicegui import ui

from ..services.budget_service import SAVINGS_CATEGORY, TRANSACTION_KINDS, TRANSFER_DIRECTIONS, TRANSFER_DIRECTION_ALIASES
from .controllers import AuthController, BudgetController, CategoryController


PAGE_CLASS = "w-full max-w-7xl mx-auto px-4 py-6 gap-5"
TOPBAR_CLASS = "topbar w-full items-start sm:items-center justify-between gap-3 bg-slate-900 text-white rounded-lg px-5 py-4 shadow-lg"
PAGE_TITLE_CLASS = "text-3xl font-bold leading-tight"
SECTION_TITLE_CLASS = "text-xl font-bold leading-snug"
PANEL_CLASS = "panel bg-white border border-slate-200 rounded-lg shadow-sm p-5"
METRIC_CLASS = "metric bg-white border border-slate-200 rounded-lg shadow-sm p-4 min-h-28 gap-1"
METRICS_GRID_CLASS = "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 w-full"
CHARTS_GRID_CLASS = "grid grid-cols-1 lg:grid-cols-2 gap-4 w-full"
WORK_GRID_CLASS = "grid grid-cols-1 xl:grid-cols-3 gap-4 w-full items-start"
SPLIT_GRID_CLASS = "grid grid-cols-1 md:grid-cols-2 gap-3 w-full"
LOGIN_SHELL_CLASS = "min-h-screen flex items-center justify-center bg-slate-100 p-6"
LOGIN_PANEL_CLASS = "w-full max-w-md bg-white border border-slate-200 rounded-lg shadow-lg p-7 gap-4"
POSITIVE_CLASS = "text-teal-700"
NEGATIVE_CLASS = "text-red-700"
BLUE_CLASS = "text-blue-700"
AMBER_CLASS = "text-amber-700"


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
            body {
                background: #f8fafc;
                color: #0f172a;
                font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }
            .nav-link { color: #dbeafe; font-weight: 600; text-decoration: none; }
            .nav-link:hover { color: white; }
            .muted { color: #64748b; }
            .metric-label { color: #64748b; font-size: 0.83rem; font-weight: 700; text-transform: uppercase; }
            .metric-value { font-size: 1.38rem; font-weight: 800; line-height: 1.25; }
            .metric-subtitle { color: #64748b; font-size: 0.88rem; line-height: 1.25; }
            .progress-block { gap: 7px; }
            .progress-track { width: 100%; height: 10px; background: #e8edf4; border-radius: 999px; overflow: hidden; }
            .progress-fill { height: 100%; border-radius: 999px; }
            .tone-green { background: #0f766e; }
            .tone-blue { background: #2563eb; }
            .tone-red { background: #dc2626; }
            .tone-amber { background: #d97706; }
            .warning-panel { background: #fff7ed; border-color: #fed7aa; }
            .tip-list { margin: 0; padding-left: 18px; color: #465264; }
            .transaction-table .q-table__top, .transaction-table .q-table__bottom { background: white; }
            .edit-dialog { width: min(560px, 92vw); border-radius: 8px; }
            </style>
            """
        )
        with ui.row().classes(TOPBAR_CLASS):
            ui.label(title).classes(PAGE_TITLE_CLASS)
            with ui.row().classes("items-center gap-4"):
                ui.link("Übersicht", "/").classes("nav-link")
                ui.link("Kategorien", "/categories").classes("nav-link")
                ui.link("Einstellungen", "/settings").classes("nav-link")
                ui.button("Logout", on_click=lambda: (self.auth.logout(), ui.navigate.to("/login"))).props("flat color=white")

    def _register_login(self) -> None:
        @ui.page("/login")
        def login_page() -> None:
            ui.add_head_html(
                """
                <style>
                body {
                    background: #f8fafc;
                    color: #0f172a;
                    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                }
                .muted { color: #64748b; }
                </style>
                """
            )
            with ui.element("div").classes(LOGIN_SHELL_CLASS):
                with ui.column().classes(LOGIN_PANEL_CLASS):
                    ui.label("Budget Tracker").classes(PAGE_TITLE_CLASS)
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

                        ui.button("Passwort speichern", on_click=setup).props("icon=save color=primary")
                        return

                    password = ui.input("Passwort", password=True, password_toggle_button=True).classes("w-full")

                    def login() -> None:
                        if self.auth.login(password.value or ""):
                            ui.navigate.to("/")
                        else:
                            ui.notify("Falsches Passwort.", type="negative")

                    password.on("keydown.enter", login)
                    ui.button("Einloggen", on_click=login).props("icon=login color=primary")

    def _register_dashboard(self) -> None:
        @ui.page("/")
        def dashboard_page() -> None:
            if not self._guard():
                return

            today = date.today()
            selected_month = {"year": today.year, "month": today.month}

            with ui.column().classes(PAGE_CLASS):
                self._shell("Budget Tracker")

                with ui.row().classes("w-full items-end gap-3"):
                    year_input = ui.number("Jahr", value=selected_month["year"], min=2000, max=2100, step=1).classes("w-32")
                    month_input = ui.number("Monat", value=selected_month["month"], min=1, max=12, step=1).classes("w-32")
                    ui.button("Monat anzeigen", on_click=lambda: refresh()).props("icon=calendar_month outline color=primary")

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
                        with ui.element("div").classes(METRICS_GRID_CLASS):
                            self._metric("Einnahmen", f"CHF {summary.income_chf:.2f}", POSITIVE_CLASS, "Gebucht im Monat")
                            self._metric("Ausgaben", f"CHF {summary.expenses_chf:.2f}", NEGATIVE_CLASS, "Gebucht im Monat")
                            free_to_spend = summary.remaining_expense_budget_chf if summary.plan else summary.balance_chf
                            free_class = POSITIVE_CLASS if free_to_spend >= 0 else NEGATIVE_CLASS
                            free_subtitle = "Restbudget" if summary.plan else "Saldo ohne Monatsplan"
                            self._metric("Noch frei", f"CHF {free_to_spend:.2f}", free_class, free_subtitle)
                            self._metric("Grösste Kategorie", largest_label, BLUE_CLASS, largest_subtitle)
                            expense_delta = round(summary.expenses_chf - previous_summary.expenses_chf, 2)
                            delta_class = POSITIVE_CLASS if expense_delta <= 0 else NEGATIVE_CLASS
                            delta_sign = "+" if expense_delta > 0 else ""
                            self._metric("Monatsvergleich", f"{delta_sign}CHF {expense_delta:.2f}", delta_class, "Ausgaben vs. Vormonat")
                            self._metric("Netto gespart", f"CHF {summary.savings_booked_chf:.2f}", BLUE_CLASS, "Umbuchungen Sparkonto")
                            health_class = POSITIVE_CLASS if summary.budget_health_score >= 80 else AMBER_CLASS
                            if summary.budget_health_score < 60:
                                health_class = NEGATIVE_CLASS
                            self._metric("Budget-Health", f"{summary.budget_health_score}/100", health_class, summary.budget_health_label)
                            self._metric("Nettovermögen", f"CHF {summary.net_worth_chf:.2f}", BLUE_CLASS, "Budgetkonto plus Sparkonto")
                            day_class = POSITIVE_CLASS if summary.available_per_day_chf >= 0 else NEGATIVE_CLASS
                            self._metric("Pro Tag frei", f"CHF {summary.available_per_day_chf:.2f}", day_class, "Bis Monatsende")

                        if summary.plan and summary.spending_budget_used_pct >= 100:
                            self._warning("Budget-Limite überschritten", "Du hast mehr Budget genutzt als geplant. Prüfe die grössten Kategorien und verschiebe falls nötig Geld vom Sparkonto zurück.")
                        elif summary.plan and summary.spending_budget_used_pct >= 80:
                            self._warning("Budget-Limite bald erreicht", "Du hast bereits über 80% deines Monatsbudgets genutzt.")

                        with ui.element("div").classes(CHARTS_GRID_CLASS):
                            with ui.column().classes(f"{PANEL_CLASS} gap-3"):
                                ui.label("Ausgaben-Verteilung").classes(SECTION_TITLE_CLASS)
                                self._pie_chart(summary.category_expenses)
                            with ui.column().classes(f"{PANEL_CLASS} gap-3"):
                                ui.label("Monatsvergleich").classes(SECTION_TITLE_CLASS)
                                self._comparison_chart(summary, previous_summary)

                        with ui.element("div").classes(WORK_GRID_CLASS):
                            with ui.column().classes(f"{PANEL_CLASS} xl:col-span-2 gap-4"):
                                ui.label("Neue Buchung").classes(SECTION_TITLE_CLASS)
                                with ui.element("div").classes(SPLIT_GRID_CLASS):
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

                                    ui.button(icon="add", on_click=add_inline_category).props("round outline color=primary").tooltip("Kategorie hinzufügen")
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

                                with ui.element("div").classes(SPLIT_GRID_CLASS):
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

                                ui.button("Buchung speichern", on_click=save_transaction).props("icon=save color=primary")

                            with ui.column().classes(f"{PANEL_CLASS} gap-4"):
                                ui.label("Monatsplan").classes(SECTION_TITLE_CLASS)
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

                                def export_csv() -> None:
                                    path = self.budget.export_csv(year, month)
                                    ui.notify(f"CSV gespeichert: {path}", type="positive")

                                with ui.row().classes("gap-2"):
                                    ui.button("Plan speichern", on_click=save_plan).props("icon=save color=primary")
                                    ui.button("PDF", on_click=export_pdf).props("icon=picture_as_pdf outline color=primary")
                                    ui.button("CSV", on_click=export_csv).props("icon=table_view outline color=primary")

                                if summary.plan:
                                    budget_tone = "tone-red" if summary.spending_budget_used_pct > 100 else "tone-green"
                                    self._progress(
                                        "Budget genutzt",
                                        summary.spending_budget_used_pct,
                                        f"Ausgaben und Umbuchungen CHF {summary.budget_used_chf:.2f} von CHF {summary.planned_expenses_chf:.2f}",
                                        budget_tone,
                                    )
                                    savings_detail = (
                                        f"Netto gespart CHF {summary.savings_booked_chf:.2f} bei Ziel CHF {summary.plan.savings_goal_chf:.2f}"
                                        if summary.savings_booked_chf >= 0
                                        else f"Vom Sparkonto geholt CHF {abs(summary.savings_booked_chf):.2f} bei Ziel CHF {summary.plan.savings_goal_chf:.2f}"
                                    )
                                    self._progress(
                                        "Sparziel erreicht",
                                        summary.savings_goal_progress_pct,
                                        savings_detail,
                                        "tone-blue",
                                    )

                                ui.separator()
                                ui.label("Kontostand und Cashflow").classes(SECTION_TITLE_CLASS)
                                with ui.element("div").classes(SPLIT_GRID_CLASS):
                                    self._mini_fact("Budgetkonto", summary.budget_cash_chf)
                                    self._mini_fact("Sparkonto", summary.savings_balance_chf)
                                self._mini_fact("Monats-Cashflow", summary.cash_flow_chf)

                                ui.separator()
                                ui.label("Ausgaben nach Kategorie").classes(SECTION_TITLE_CLASS)
                                top_categories = sorted(summary.category_expenses.items(), key=lambda item: item[1], reverse=True)[:5]
                                if not top_categories:
                                    ui.label("Noch keine Ausgaben in diesem Monat.").classes("muted")
                                for category_name, spent in top_categories:
                                    share = round((spent / summary.expenses_chf) * 100, 1) if summary.expenses_chf else 0.0
                                    self._category_bar(category_name, spent, share)

                                ui.separator()
                                ui.label("Wiederkehrende Ausgaben").classes(SECTION_TITLE_CLASS)
                                if not summary.recurring_expenses:
                                    ui.label("Noch nicht genug Historie für sichere Erkennung.").classes("muted")
                                for recurring in summary.recurring_expenses:
                                    ui.label(
                                        f"{recurring.name}: CHF {recurring.monthly_amount_chf:.2f}/Monat "
                                        f"(ca. CHF {recurring.yearly_amount_chf:.2f}/Jahr)"
                                    ).classes("muted")

                                ui.separator()
                                ui.label("Spartipps").classes(SECTION_TITLE_CLASS)
                                with ui.element("ul").classes("tip-list"):
                                    for tip in self._spending_tips(summary, previous_summary):
                                        with ui.element("li").classes("mb-1"):
                                            ui.label(tip)

                    table_container.clear()
                    with table_container:
                        with ui.column().classes(f"{PANEL_CLASS} w-full gap-3"):
                            ui.label("Monatliche Buchungen").classes(SECTION_TITLE_CLASS)
                            all_rows = [
                                {
                                    "id": transaction.id,
                                    "date": transaction.booking_date.strftime("%d.%m.%Y"),
                                    "raw_date": transaction.booking_date.isoformat(),
                                    "kind": transaction.kind,
                                    "direction": TRANSFER_DIRECTION_ALIASES.get(transaction.transfer_direction, transaction.transfer_direction or ""),
                                    "category": "Sparkonto" if transaction.kind == "Umbuchung" else (transaction.category.name if transaction.category else "Unbekannt"),
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
                            with ui.element("div").classes(SPLIT_GRID_CLASS):
                                search_input = ui.input("Suche", placeholder="Notiz, Kategorie, Typ").props("clearable").classes("w-full")
                                kind_filter = ui.select(["Alle", *TRANSACTION_KINDS], value="Alle", label="Typ filtern").classes("w-full")
                            with ui.element("div").classes(SPLIT_GRID_CLASS):
                                category_options = ["Alle", *sorted({row["category"] for row in all_rows})]
                                category_filter = ui.select(category_options, value="Alle", label="Kategorie filtern").classes("w-full")
                                ui.label("").classes("w-full")
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
                                    ui.label(f"{len(filtered_rows)} von {len(all_rows)} Buchungen").classes("muted")
                                    table = ui.table(columns=columns, rows=filtered_rows, row_key="id").classes("transaction-table w-full")
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
                    with dialog, ui.card().classes("edit-dialog rounded-lg gap-4"):
                        ui.label("Buchung bearbeiten").classes(SECTION_TITLE_CLASS)
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
                            ui.button("Speichern", on_click=save_edit).props("icon=save color=primary")
                            ui.button("Abbrechen", on_click=dialog.close).props("flat")
                    dialog.open()

                refresh()

    def _register_categories(self) -> None:
        @ui.page("/categories")
        def categories_page() -> None:
            if not self._guard():
                return
            with ui.column().classes(PAGE_CLASS):
                self._shell("Kategorien")
                with ui.column().classes(f"{PANEL_CLASS} gap-4"):
                    ui.label("Kategorien verwalten").classes(SECTION_TITLE_CLASS)
                    name = ui.input("Neue Kategorie").classes("w-full max-w-md")
                    list_container = ui.column().classes("w-full")

                    def refresh_list() -> None:
                        list_container.clear()
                        with list_container:
                            rows = [{"name": category} for category in self.categories.list_categories()]
                            ui.table(
                                columns=[{"name": "name", "label": "Kategorie", "field": "name", "align": "left"}],
                                rows=rows,
                            ).classes("w-full max-w-xl").props("flat bordered")

                    def add() -> None:
                        try:
                            created = self.categories.add_category(name.value or "")
                        except ValueError as exc:
                            ui.notify(str(exc), type="warning")
                            return
                        name.value = ""
                        ui.notify(f"Kategorie {created} hinzugefügt.", type="positive")
                        refresh_list()

                    ui.button("Kategorie hinzufügen", on_click=add).props("icon=add color=primary")
                    refresh_list()

    def _register_settings(self) -> None:
        @ui.page("/settings")
        def settings_page() -> None:
            if not self._guard():
                return
            with ui.column().classes(PAGE_CLASS):
                self._shell("Einstellungen")
                with ui.column().classes(f"{PANEL_CLASS} gap-4"):
                    ui.label("Passwort ändern").classes(SECTION_TITLE_CLASS)
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

                ui.button("Passwort speichern", on_click=change).props("icon=save color=primary")

    @staticmethod
    def _previous_month(year: int, month: int) -> tuple[int, int]:
        if month == 1:
            return year - 1, 12
        return year, month - 1

    @staticmethod
    def _warning(title: str, message: str) -> None:
        with ui.column().classes(f"{PANEL_CLASS} warning-panel gap-1"):
            ui.label(title).classes(f"{SECTION_TITLE_CLASS} {AMBER_CLASS}")
            ui.label(message).classes("muted")

    @staticmethod
    def _pie_chart(category_expenses: dict[str, float]) -> None:
        data = [{"name": name, "value": value} for name, value in sorted(category_expenses.items(), key=lambda item: item[1], reverse=True)]
        if not data:
            ui.label("Noch keine Ausgaben für ein Diagramm.").classes("muted")
            return
        ui.echart(
            {
                "tooltip": {"trigger": "item"},
                "legend": {"bottom": 0, "left": "center"},
                "series": [
                    {
                        "type": "pie",
                        "radius": ["42%", "70%"],
                        "avoidLabelOverlap": True,
                        "itemStyle": {"borderRadius": 6, "borderColor": "#fff", "borderWidth": 2},
                        "label": {"formatter": "{b}: {d}%"},
                        "data": data,
                    }
                ],
            }
        ).classes("w-full h-72")

    @staticmethod
    def _comparison_chart(summary, previous_summary) -> None:
        ui.echart(
            {
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": ["Vormonat", "Aktuell"]},
                "yAxis": {"type": "value"},
                "series": [
                    {
                        "name": "Ausgaben",
                        "type": "bar",
                        "data": [previous_summary.expenses_chf, summary.expenses_chf],
                        "itemStyle": {"color": "#b42318"},
                    },
                    {
                        "name": "Budget genutzt",
                        "type": "bar",
                        "data": [previous_summary.budget_used_chf, summary.budget_used_chf],
                        "itemStyle": {"color": "#2563eb"},
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
    def _metric(label: str, value: str, value_class: str, subtitle: str = "") -> None:
        with ui.column().classes(METRIC_CLASS):
            ui.label(label).classes("metric-label")
            ui.label(value).classes(f"metric-value {value_class}")
            if subtitle:
                ui.label(subtitle).classes("metric-subtitle")

    @staticmethod
    def _progress(label: str, percent: float, detail: str, tone: str) -> None:
        safe_percent = max(0.0, min(percent, 100.0))
        with ui.column().classes("progress-block w-full"):
            with ui.row().classes("w-full items-center justify-between"):
                ui.label(label).classes("font-bold")
                ui.label(f"{percent:.1f}%").classes("muted")
            with ui.element("div").classes("progress-track"):
                ui.element("div").classes(f"progress-fill {tone}").style(f"width: {safe_percent}%;")
            ui.label(detail).classes("muted text-xs")

    @staticmethod
    def _mini_fact(label: str, amount: float) -> None:
        amount_class = POSITIVE_CLASS if amount >= 0 else NEGATIVE_CLASS
        with ui.column().classes("gap-1"):
            ui.label(label).classes("font-bold")
            ui.label(f"CHF {amount:.2f}").classes(amount_class)

    @staticmethod
    def _category_bar(category_name: str, spent: float, share: float) -> None:
        safe_share = max(0.0, min(share, 100.0))
        with ui.column().classes("progress-block w-full"):
            with ui.row().classes("w-full items-center justify-between gap-2"):
                ui.label(category_name).classes("font-bold")
                ui.label(f"CHF {spent:.2f} · {share:.1f}%").classes("muted")
            with ui.element("div").classes("progress-track"):
                ui.element("div").classes("progress-fill tone-amber").style(f"width: {safe_share}%;")
