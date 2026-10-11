
import sqlite3

DB_NAME = "spendwise.db"


# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

def get_connection():
    return sqlite3.connect(DB_NAME)


# -----------------------------------
# CREATE TRANSACTIONS TABLE
# -----------------------------------

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            description TEXT
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------------
# ADD TRANSACTION
# -----------------------------------

def add_transaction(date, trans_type, category, amount, description):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
        (date, type, category, amount, description)
        VALUES (?, ?, ?, ?, ?)
    """, (date, trans_type, category, amount, description))

    conn.commit()
    conn.close()


# -----------------------------------
# GET ALL TRANSACTIONS
# -----------------------------------

def get_transactions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY date DESC, id DESC
    """)

    data = cursor.fetchall()

    conn.close()
    return data


# -----------------------------------
# DELETE TRANSACTION
# -----------------------------------

def delete_transaction(transaction_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        DELETE FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    conn.commit()
    conn.close()


# -----------------------------------
# CREATE BUDGET TABLE
# -----------------------------------

def create_budget_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            month TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0),
            UNIQUE(month, category)
        )
    """)

    conn.commit()
    conn.close()


# -----------------------------------
# SAVE OR UPDATE BUDGET
# -----------------------------------

def save_budget(month, category, amount):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO budgets (month, category, amount)
        VALUES (?, ?, ?)
        ON CONFLICT(month, category)
        DO UPDATE SET amount = excluded.amount
    """, (month, category, amount))

    conn.commit()
    conn.close()


# -----------------------------------
# GET MONTHLY BUDGETS
# -----------------------------------

def get_budgets(month):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, amount
        FROM budgets
        WHERE month = ?
        ORDER BY category
    """, (month,))

    budgets = cursor.fetchall()

    conn.close()
    return budgets
