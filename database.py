import psycopg

class DatabaseManager:
    def __init__(self, dsn: str):
        self.dsn = dsn

    def get_connection(self):
        return psycopg.connect(self.dsn)

    def init_schema(self):
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS categories (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) UNIQUE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS expenses (
                        id SERIAL PRIMARY KEY,
                        amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
                        category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE RESTRICT,
                        description TEXT,
                        expense_date DATE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS incomes (
                        id SERIAL PRIMARY KEY,
                        amount NUMERIC(10, 2) NOT NULL CHECK (amount > 0),
                        description TEXT,
                        income_date DATE NOT NULL
                    );
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expenses_date 
                    ON expenses (expense_date);
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_incomes_date 
                    ON incomes (income_date);
                """)
            conn.commit()
