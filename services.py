import calendar
from collections import defaultdict
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Tuple
import psycopg

from models import (
    Category,
    Expense,
    CategoryBreakdown,
    CategoryForecast,
    Income,
    MonthlyForecastReport,
)
from repositories import CategoryRepository, ExpenseRepository, IncomeRepository


class ExpenseTrackerService:
    def __init__(self, category_repo: CategoryRepository, expense_repo: ExpenseRepository, income_repo: IncomeRepository):
        self.category_repo = category_repo
        self.expense_repo = expense_repo
        self.income_repo = income_repo

    def create_category(self, raw_name: str) -> Category:
        clean_name = raw_name.strip().title()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        if len(clean_name) > 100:
            raise ValueError("Category name cannot exceed 100 characters.")
        try:
            return self.category_repo.create(clean_name)
        except psycopg.errors.UniqueViolation:
            raise ValueError(f"Category '{clean_name}' already exists.")

    def list_categories(self) -> List[Category]:
        return self.category_repo.get_all()

    def record_expense(
        self, amount: Decimal, category_id: int, expense_date: date, description: str = ""
    ) -> Tuple[Expense, Decimal, List[CategoryBreakdown]]:
        if amount <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        valid_ids = {c.id for c in self.category_repo.get_all()}
        if category_id not in valid_ids:
            raise ValueError("Selected category ID does not exist.")

        new_expense = Expense(
            id=None,
            amount=amount,
            category_id=category_id,
            expense_date=expense_date,
            description=description.strip()
        )
        saved_expense = self.expense_repo.add(new_expense)
        total, breakdown = self.get_monthly_report(expense_date.year, expense_date.month)
        return saved_expense, total, breakdown
    
    def record_income(
        self, amount: Decimal, income_date: date, description: str = ""
    ) -> Tuple[Income, Decimal]:
        if amount <= 0:
            raise ValueError("Income amount must be greater than zero.")

        new_income = Income(
            id=None,
            amount=amount,
            income_date=income_date,
            description=description.strip()
        )
        saved_income = self.income_repo.add(new_income)
        monthly_total = self.get_monthly_income(income_date.year, income_date.month)
        return saved_income, monthly_total

    def get_monthly_income(self, year: int, month: int) -> Decimal:
            '''
            Retrieves the total income for a specified month and year.
            Returns 0.00 if no income records are found for that month.
            '''
            total_income = self.income_repo.get_monthly_total(year, month)

            if total_income[0][0] == 0:
                return Decimal("0.00")
                
            return total_income[0][0]

    def get_monthly_report(self, year: int, month: int) -> Tuple[Decimal, List[CategoryBreakdown]]:
        rows = self.expense_repo.get_monthly_totals_by_category(year, month)
        total_spent = sum((amount for _, amount in rows), Decimal("0.00"))

        if total_spent == 0:
            return Decimal("0.00"), []

        breakdowns = [
            CategoryBreakdown(
                category_name=name,
                total_spent=cat_total,
                percentage=float((cat_total / total_spent) * 100)
            )
            for name, cat_total in rows
        ]
        return total_spent, breakdowns

class ForecastService:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def generate_forecast(self, months_back: int = 3) -> MonthlyForecastReport:
        """
        Generates a spending forecast for the rest of the current month and
        predicts next month's expenses per category based on historical trends.
        """
        today = date.today()
        current_ym = (today.year, today.month)

        # 1. Calculate Current Month Run-Rate Pace
        # Fetch category spending for the ongoing month and sum the total
        current_rows = self.expense_repo.get_monthly_totals_by_category(today.year, today.month)
        current_spent = sum((amount for _, amount in current_rows), Decimal("0.00"))

        # Determine how many days are in the current month and how many have passed
        _, days_in_month = calendar.monthrange(today.year, today.month)
        days_elapsed = max(today.day, 1)

        # Calculate average daily spend so far and project it across the full month
        daily_pace = current_spent / Decimal(days_elapsed)
        current_projected = (daily_pace * Decimal(days_in_month)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 2. Gather Completed Historical Months
        # Pull historical data and filter out the incomplete current month
        raw_history = self.expense_repo.get_historical_monthly_category_totals(months_back=months_back)
        completed_months = sorted({(yr, mo) for yr, mo, _, _ in raw_history if (yr, mo) != current_ym})

        # Group historical totals by category -> {(year, month): total_amount}
        category_history = defaultdict(dict)

        for yr, mo, cat_name, total in raw_history:
            if (yr, mo) != current_ym:
                category_history[cat_name][(yr, mo)] = total
        
        # Fallback: If there are no completed past months, base next month's forecast
        # purely on the current month's projected run-rate
        if not completed_months:
            fallback_forecasts = [
                CategoryForecast(
                    category_name=name,
                    last_month_spent=Decimal("0.00"),
                    historical_avg=spent,
                    # quantize rounds a Decimal number to a fixed number of decimal places
                    predicted_next_month=((spent / Decimal(days_elapsed)) * Decimal(days_in_month)).quantize(Decimal("0.01")),
                    trend_direction="New"
                )
                for name, spent in current_rows
            ]
            next_total = sum((f.predicted_next_month for f in fallback_forecasts), Decimal("0.00"))
            return MonthlyForecastReport(
                current_month_spent=current_spent,
                current_month_projected=current_projected,
                next_month_predicted_total=next_total,
                category_forecasts=fallback_forecasts
            )

        # 3. Predict Next Month per Category
        category_forecasts = []

        # Identify the most recent completed month (the last item in the sorted list)
        last_ym = completed_months[-1]

        for cat_name, month_map in sorted(category_history.items()):
            # Build a chronological list of spending for all completed months (defaulting to $0.00 if missing)
            series = [month_map.get(ym, Decimal("0.00")) for ym in completed_months]
            last_month_val = month_map.get(last_ym, Decimal("0.00"))

            # Calculate simple historical average
            hist_avg = (sum(series) / Decimal(len(series))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            # Calculate a linearly weighted moving average (more recent months carry higher weight)
            weights = [Decimal(i + 1) for i in range(len(series))]
            weighted_avg = sum(val * w for val, w in zip(series, weights)) / sum(weights)

            # Adjust prediction based on recent momentum if at least 2 months of history exist
            if len(series) >= 2:
                prior_series = series[:-1]
                latest_val = series[-1]
                prior_avg = sum(prior_series) / Decimal(len(prior_series))

                # Compare the latest month against the average of prior months and apply a 25% momentum factor
                diff = latest_val - prior_avg
                raw_prediction = weighted_avg + (diff * Decimal("0.25"))

                # Flag trend direction if the latest month deviates by more than 10% from the prior average
                if diff > prior_avg * Decimal("0.10"):
                    trend = "Up"
                elif diff < -prior_avg * Decimal("0.10"):
                    trend = "Down"
                else:
                    trend = "Stable"
            else:
                # With only 1 month of history, use the weighted average directly without trend adjustments
                raw_prediction = weighted_avg
                trend = "New"

            # Prevent negative spending predictions and round to standard currency format
            predicted_val = max(Decimal("0.00"), raw_prediction).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            category_forecasts.append(
                CategoryForecast(
                    category_name=cat_name,
                    last_month_spent=last_month_val,
                    historical_avg=hist_avg,
                    predicted_next_month=predicted_val,
                    trend_direction=trend
                )
            )

        # Sort categories from highest predicted spend to lowest
        category_forecasts.sort(key=lambda x: x.predicted_next_month, reverse=True)
        next_month_total = sum((f.predicted_next_month for f in category_forecasts), Decimal("0.00"))

        return MonthlyForecastReport(
            current_month_spent=current_spent,
            current_month_projected=current_projected,
            next_month_predicted_total=next_month_total,
            category_forecasts=category_forecasts
        )