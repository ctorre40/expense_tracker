from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional, List


@dataclass
class Category:
    id: Optional[int]
    name: str


@dataclass
class Expense:
    id: Optional[int]
    amount: Decimal
    category_id: int
    expense_date: date
    description: str = ""

@dataclass
class Income:
    id: Optional[int]
    amount: Decimal
    income_date: date
    description: str = ""

@dataclass
class CategoryBreakdown:
    category_name: str
    total_spent: Decimal
    percentage: float


@dataclass
class CategoryForecast:
    category_name: str
    last_month_spent: Decimal
    historical_avg: Decimal
    predicted_next_month: Decimal
    trend_direction: str


@dataclass
class MonthlyForecastReport:
    current_month_spent: Decimal
    current_month_projected: Decimal
    next_month_predicted_total: Decimal
    category_forecasts: List[CategoryForecast]
