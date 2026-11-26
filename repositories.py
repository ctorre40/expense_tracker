from decimal import Decimal
from typing import List, Tuple
import psycopg
from models import Category, Expense, Income
from database import DatabaseManager

class CategoryRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def create(self, name: str) -> Category:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO categories (name) VALUES (%s) RETURNING id, name;",
                    (name,)
                )
                row = cur.fetchone()
                conn.commit()
                return Category(id=row[0], name=row[1])

    def get_all(self) -> List[Category]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name FROM categories ORDER BY name;")
                return [Category(id=r[0], name=r[1]) for r in cur.fetchall()]


class ExpenseRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, expense: Expense) -> Expense:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO expenses (amount, category_id, description, expense_date)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (expense.amount, expense.category_id, expense.description, expense.expense_date)
                )
                expense.id = cur.fetchone()[0]
                conn.commit()
                return expense

    def get_monthly_totals_by_category(self, year: int, month: int) -> List[Tuple[str, Decimal]]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT c.name, COALESCE(SUM(e.amount), 0)
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.id
                    WHERE EXTRACT(YEAR FROM e.expense_date) = %s
                      AND EXTRACT(MONTH FROM e.expense_date) = %s
                    GROUP BY c.name
                    ORDER BY SUM(e.amount) DESC;
                    """,
                    (year, month)
                )
                return cur.fetchall()        

    def get_historical_monthly_category_totals(self, months_back: int = 6) -> List[Tuple[int, int, str, Decimal]]:
        """Returns (year, month, category_name, total_spent) for the past N months."""
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT 
                        EXTRACT(YEAR FROM e.expense_date)::int AS yr,
                        EXTRACT(MONTH FROM e.expense_date)::int AS mo,
                        c.name,
                        COALESCE(SUM(e.amount), 0)
                    FROM expenses e
                    JOIN categories c ON e.category_id = c.id
                    WHERE e.expense_date >= (DATE_TRUNC('month', CURRENT_DATE) - (%s || ' months')::interval)
                    GROUP BY yr, mo, c.name
                    ORDER BY yr ASC, mo ASC, c.name ASC;
                    """,
                    (months_back,)
                )
                return cur.fetchall()

class IncomeRepository:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def add(self, income: Income) -> Income:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO incomes (amount, description, income_date)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (income.amount, income.description, income.income_date)
                )
                income.id = cur.fetchone()[0]
                conn.commit()
                return income

    def get_monthly_total(self, year: int, month: int) -> List[Tuple[str, Decimal]]:
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COALESCE(SUM(i.amount), 0)
                    FROM incomes i
                    WHERE EXTRACT(YEAR FROM i.income_date) = %s
                    AND EXTRACT(MONTH FROM i.income_date) = %s;
                    """,
                    (year, month)
                )
                return cur.fetchall()