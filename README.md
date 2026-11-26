# Expense Tracker

A desktop expense and budget tracker built to log income and expenses and forecast future spending based on historical data.

## Features

* **Income Tracking:** Log monthly income entries with dates and descriptions.
* **Expense Tracking:** Log monthly expense entries with dates and descriptions.
* **Spending Forecast:** Analyzes the previous three months of expenses to project future spending habits and identify whether spending is trending up, trending down, or remaining stable.

## Tech Stack

* **Language:** Python 3.9.6
* **GUI Framework:** PySide6
* **Database:** PostgreSQL

## Prerequisites

* Python 3.9 or higher
* `pip` (Python package manager)
* PostgreSQL instance (local or hosted)
* Refer to [Python.org](https://www.python.org/) for help installing Python.

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ctorre40
   cd expense_tracker
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables:**
   Create a `.env` file in the root directory and add your PostgreSQL database credentials (refer to `.env.example` for the expected format).

## Usage

Run the main application entry point:

```bash
python main.py
```

## Project Structure

```text
expense_tracker/
├── main.py             # Application entry point
├── gui.py              # Display logic
├── services.py         # Business logic and forecasting
├── models.py           # Data models
├── database.py         # Database connection and schema setup
├── repositories.py     # Database queries
├── requirements.txt    # Project dependencies
└── README.md           # Project documentation
```

## Roadmap / In Progress (11/2026)

* **Testing & Validation:** Build a test suite to verify forecast accuracy and enforce secure input validation.
* **Web Deployment:** Adapt the application for deployment on a personal website.
* **Additional GUI opertations:** Add a way for the user to remove and edit existing entries

## Feedback & Issues

Thank you for viewing! If you have any questions or encounter any bugs, please feel free to open an issue or reach out.
