from dotenv import load_dotenv
import os
import sys
from database import DatabaseManager
from gui import ExpenseWindow
from repositories import CategoryRepository, ExpenseRepository, IncomeRepository
from services import ExpenseTrackerService, ForecastService
from PySide6.QtWidgets import (QApplication)

if __name__ == "__main__":
    load_dotenv()
    DSN = os.getenv("DATABASE_URL")

    if not DSN:
        raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

    db_manager = DatabaseManager(DSN)
    db_manager.init_schema()
    category_repo = CategoryRepository(db_manager)
    expense_repo = ExpenseRepository(db_manager)
    income_repo = IncomeRepository(db_manager)
    tracker_service = ExpenseTrackerService(category_repo, expense_repo, income_repo)
    forecast_service = ForecastService(expense_repo)

    app = QApplication(sys.argv)

    window = ExpenseWindow(tracker_service, forecast_service)
    window.show()
    sys.exit(app.exec())