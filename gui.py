from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from services import ExpenseTrackerService, ForecastService
from PySide6.QtCore import Qt, QDate, QRegularExpression
from PySide6.QtGui import QFont, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QMainWindow,    QWidget,
    QVBoxLayout,    QHBoxLayout,    QFormLayout,
    QGroupBox,    QLineEdit,    QComboBox,
    QDateEdit,    QPushButton,    QLabel,
    QTableWidget,    QTableWidgetItem,    QHeaderView,
    QMessageBox,    QTabWidget,
)

class ExpenseWindow(QMainWindow):
    def __init__(self, tracker_service: ExpenseTrackerService, forecast_service: ForecastService):
        super().__init__()
        self.tracker_service = tracker_service
        self.forecast_service = forecast_service

        self.setWindowTitle("Expense Tracker & Forecaster")
        self.resize(740, 660)

        self._build_ui()
        self._refresh_categories()
        self._refresh_breakdown()
        self._loadMonthlyIncomeTotal()
        self._refresh_forecast()

    def _build_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Build both tabs
        tracker_tab = self._build_tracker_tab()
        forecast_tab = self._build_forecast_tab()

        self.tabs.addTab(tracker_tab, "Log & Breakdown")
        self.tabs.addTab(forecast_tab, "Future Predictions")

    def _build_tracker_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Section 1: Create Category ---
        cat_group = QGroupBox("1. Manage Categories")
        cat_layout = QHBoxLayout(cat_group)

        self.new_cat_input = QLineEdit()
        self.new_cat_input.setPlaceholderText("e.g., Groceries, Rent, Dining...")
        self.new_cat_input.returnPressed.connect(self.on_create_category)

        create_cat_btn = QPushButton("Create Category")
        create_cat_btn.clicked.connect(self.on_create_category)

        cat_layout.addWidget(QLabel("New Category:"))
        cat_layout.addWidget(self.new_cat_input)
        cat_layout.addWidget(create_cat_btn)
        layout.addWidget(cat_group)

        # --- Section 2: Log Expense ---
        exp_group = QGroupBox("2. Log Expense")
        exp_layout = QFormLayout(exp_group)

        self.expense_amount_input = QLineEdit()
        self.expense_amount_input.setPlaceholderText("0.00")

        # Matches digits with optional decimal point and up to 2 decimal places (e.g., "100", "10.5", "10.50")
        expense_regex = QRegularExpression(r"^\d+(\.\d{0,2})?$")
        expense_validator = QRegularExpressionValidator(expense_regex, self.expense_amount_input)
        self.expense_amount_input.setValidator(expense_validator)

        self.category_combo = QComboBox()

        self.expense_date_input = QDateEdit()
        self.expense_date_input.setCalendarPopup(True)
        self.expense_date_input.setDisplayFormat("yyyy-MM-dd")
        self.expense_date_input.setDate(QDate.currentDate())

        self.expense_desc_input = QLineEdit()
        self.expense_desc_input.setPlaceholderText("Optional note...")
        self.expense_desc_input.returnPressed.connect(self.on_add_expense)

        save_exp_btn = QPushButton("Save Expense")
        save_exp_btn.clicked.connect(self.on_add_expense)

        exp_layout.addRow("Amount ($):", self.expense_amount_input)
        exp_layout.addRow("Category:", self.category_combo)
        exp_layout.addRow("Date:", self.expense_date_input)
        exp_layout.addRow("Description:", self.expense_desc_input)
        exp_layout.addRow(save_exp_btn)
        layout.addWidget(exp_group)

        # --- Section 3: Log Income ---
        inc_group = QGroupBox("3. Log Income")
        inc_layout = QFormLayout(inc_group)

        self.income_amount_input = QLineEdit()
        self.income_amount_input.setPlaceholderText("0.00")

        # Matches digits with optional decimal point and up to 2 decimal places (e.g., "100", "10.5", "10.50")
        income_regex = QRegularExpression(r"^\d+(\.\d{0,2})?$")
        income_validator = QRegularExpressionValidator(income_regex, self.income_amount_input)
        self.income_amount_input.setValidator(income_validator)

        self.income_date_input = QDateEdit()
        self.income_date_input.setCalendarPopup(True)
        self.income_date_input.setDisplayFormat("yyyy-MM-dd")
        self.income_date_input.setDate(QDate.currentDate())

        self.income_desc_input = QLineEdit()
        self.income_desc_input.setPlaceholderText("Optional note...")
        self.income_desc_input.returnPressed.connect(self.on_add_income)

        save_inc_btn = QPushButton("Save Income")
        save_inc_btn.clicked.connect(self.on_add_income)

        inc_layout.addRow("Amount ($):", self.income_amount_input)
        inc_layout.addRow("Date:", self.income_date_input)
        inc_layout.addRow("Description:", self.income_desc_input)
        inc_layout.addRow(save_inc_btn)

        #Display Monthly Income Total
        self.total_label_monthly_income = QLabel("Monthly Income: $0.00")
        bold_font_2 = QFont()
        bold_font_2.setBold(True)
        bold_font_2.setPointSize(12)
        self.total_label_monthly_income.setFont(bold_font_2)
        self.total_label_monthly_income.setAlignment(Qt.AlignRight)        

        layout.addWidget(inc_group)
        layout.addWidget(self.total_label_monthly_income)

        # --- Section 4: Monthly Breakdown ---
        report_group = QGroupBox("3. Monthly Category Breakdown")
        report_layout = QVBoxLayout(report_group)

        filter_bar = QHBoxLayout()
        self.month_input = QDateEdit()
        self.month_input.setDisplayFormat("yyyy-MM")
        self.month_input.setDate(QDate.currentDate())

        load_month_btn = QPushButton("Load Month")
        load_month_btn.clicked.connect(self._refresh_breakdown)

        self.total_label = QLabel("Total: $0.00")
        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(12)
        self.total_label.setFont(bold_font)

        filter_bar.addWidget(QLabel("Month:"))
        filter_bar.addWidget(self.month_input)
        filter_bar.addWidget(load_month_btn)
        filter_bar.addStretch()
        filter_bar.addWidget(self.total_label)
        report_layout.addLayout(filter_bar)

        # Breakdown Table
        self.breakdown_table = QTableWidget(0, 3)
        self.breakdown_table.setHorizontalHeaderLabels(["Category", "Total Spent", "% of Month"])
        self.breakdown_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.breakdown_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.breakdown_table.verticalHeader().setVisible(False)

        header = self.breakdown_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        report_layout.addWidget(self.breakdown_table)
        layout.addWidget(report_group)
        return tab

    def _build_forecast_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # --- Summary Card ---
        summary_group = QGroupBox("Spending Pace & Next Month Outlook")
        summary_layout = QFormLayout(summary_group)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(11)

        self.current_pace_label = QLabel("$0.00 spent so far -> $0.00 projected by month-end")
        self.next_month_total_label = QLabel("$0.00")
        self.next_month_total_label.setFont(bold_font)

        refresh_btn = QPushButton("Recalculate Forecast")
        refresh_btn.clicked.connect(self._refresh_forecast)

        summary_layout.addRow("Current Month Pace:", self.current_pace_label)
        summary_layout.addRow("Predicted Next Month Total:", self.next_month_total_label)
        summary_layout.addRow(refresh_btn)
        layout.addWidget(summary_group)

        # --- Category Forecast Table ---
        table_group = QGroupBox("Category Predictions (Based on Up to 3 Months History)")
        table_layout = QVBoxLayout(table_group)

        self.forecast_table = QTableWidget(0, 5)
        self.forecast_table.setHorizontalHeaderLabels([
            "Category",
            "Last Month",
            "Historical Avg",
            "Predicted Next Mo",
            "Trend",
        ])
        self.forecast_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.forecast_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.forecast_table.verticalHeader().setVisible(False)

        f_header = self.forecast_table.horizontalHeader()
        f_header.setSectionResizeMode(0, QHeaderView.Stretch)

        for col in range(1, 5):
            f_header.setSectionResizeMode(col, QHeaderView.ResizeToContents)

        table_layout.addWidget(self.forecast_table)
        layout.addWidget(table_group)
        return tab

    def _refresh_categories(self):
        current_id = self.category_combo.currentData()
        self.category_combo.clear()

        categories = self.tracker_service.list_categories()
        for cat in categories:
            self.category_combo.addItem(cat.name, userData=cat.id)

        if current_id is not None:
            index = self.category_combo.findData(current_id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)

    def _refresh_breakdown(self):
        selected_qdate = self.month_input.date()
        year = selected_qdate.year()
        month = selected_qdate.month()

        total, breakdowns = self.tracker_service.get_monthly_report(year, month)
        self.total_label.setText(f"Total: ${total:,.2f}")

        self._refresh_monthly_income_total()

        self.breakdown_table.setRowCount(len(breakdowns))
        for row_idx, item in enumerate(breakdowns):
            cat_item = QTableWidgetItem(item.category_name)

            spent_item = QTableWidgetItem(f"${item.total_spent:,.2f}")
            spent_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            pct_item = QTableWidgetItem(f"{item.percentage:.1f}%")
            pct_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            self.breakdown_table.setItem(row_idx, 0, cat_item)
            self.breakdown_table.setItem(row_idx, 1, spent_item)
            self.breakdown_table.setItem(row_idx, 2, pct_item)

    def _loadMonthlyIncomeTotal(self):
        selected_qdate = self.month_input.date()
        year = selected_qdate.year()
        month = selected_qdate.month()

        monthly_income_total = self.tracker_service.get_monthly_income(year, month)
        self.total_label_monthly_income.setText(f"Monthly Income: ${monthly_income_total:,.2f}")

    def _refresh_monthly_income_total(self):
        selected_qdate = self.month_input.date()
        year = selected_qdate.year()
        month = selected_qdate.month()

        monthly_income_total = self.tracker_service.get_monthly_income(year, month)
        self.total_label_monthly_income.setText(f"Monthly Income: ${monthly_income_total:,.2f}")

    def _refresh_forecast(self):
        report = self.forecast_service.generate_forecast(months_back=3)

        self.current_pace_label.setText(
            f"${report.current_month_spent:,.2f} spent so far  ->  "
            f"${report.current_month_projected:,.2f} projected by month-end"
        )
        self.next_month_total_label.setText(f"${report.next_month_predicted_total:,.2f}")

        self.forecast_table.setRowCount(len(report.category_forecasts))
        for row_idx, item in enumerate(report.category_forecasts):
            cat_item = QTableWidgetItem(item.category_name)

            last_mo_item = QTableWidgetItem(f"${item.last_month_spent:,.2f}")
            last_mo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            avg_item = QTableWidgetItem(f"${item.historical_avg:,.2f}")
            avg_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            pred_item = QTableWidgetItem(f"${item.predicted_next_month:,.2f}")
            pred_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            trend_item = QTableWidgetItem(item.trend_direction)
            trend_item.setTextAlignment(Qt.AlignCenter)

            self.forecast_table.setItem(row_idx, 0, cat_item)
            self.forecast_table.setItem(row_idx, 1, last_mo_item)
            self.forecast_table.setItem(row_idx, 2, avg_item)
            self.forecast_table.setItem(row_idx, 3, pred_item)
            self.forecast_table.setItem(row_idx, 4, trend_item)

    def on_create_category(self):
        name = self.new_cat_input.text()
        if not name:
            QMessageBox.warning(self, "Invalid Category", "Please enter a category name.")
            return
        if len(name) > 100:
            QMessageBox.warning(self, "Invalid Category", "Category name must be 100 characters or less.")
            return
        try:
            cat = self.tracker_service.create_category(name)
            self.new_cat_input.clear()
            self._refresh_categories()
            index = self.category_combo.findData(cat.id)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
                QMessageBox.information(self, "Success", f"Category '{cat.name}' created.")
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Category", str(e))

    def on_add_income(self):        
        '''
        Adds a new income entry to the tracker.
        Validates the input amount and date, then records the income using the tracker service.
        Updates the monthly income total label after successful addition.'''
        try:
            amount = Decimal(self.income_amount_input.text().strip())
            amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if amount <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid positive dollar amount.")
                return
            if amount > Decimal('99999999.99'):
                QMessageBox.warning(self, "Invalid Amount", "Amount exceeds maximum allowed value of $99,999,999.99")
                return
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid dollar amount.")
            return
        
        qdate = self.income_date_input.date()
        inc_date = date(qdate.year(), qdate.month(), qdate.day())
        desc = self.income_desc_input.text()

        try:
            #saves and returns total for the month
            income_obj, monthly_total = self.tracker_service.record_income(amount, inc_date, desc)

            self.income_amount_input.clear()
            self.income_desc_input.clear()
            self.month_input.setDate(qdate)
            self.total_label_monthly_income.setText(f"Monthly Income: ${monthly_total:,.2f}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))

    def on_add_expense(self):
        cat_id = self.category_combo.currentData()
        if cat_id is None:
            QMessageBox.warning(self, "Missing Category", "Please create and select a category first.")
            return
        try:
            amount = Decimal(self.expense_amount_input.text().strip())
            amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if amount <= 0:
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid positive dollar amount.")
                return
            if amount > Decimal('99999999.99'):
                QMessageBox.warning(self, "Invalid Amount", "Amount exceeds maximum allowed value of $99,999,999.99")
                return
        except InvalidOperation:
            QMessageBox.warning(self, "Invalid Amount", "Please enter a valid dollar amount.")
            return
        
        qdate = self.expense_date_input.date()
        exp_date = date(qdate.year(), qdate.month(), qdate.day())
        desc = self.expense_desc_input.text()

        try:
            self.tracker_service.record_expense(amount, cat_id, exp_date, desc)
            self.expense_amount_input.clear()
            self.expense_desc_input.clear()
            self.month_input.setDate(qdate)
            self._refresh_breakdown()
            self._refresh_forecast()
        except ValueError as e:
            QMessageBox.warning(self, "Error", str(e))