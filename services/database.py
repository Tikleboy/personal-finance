import os
import sqlite3

# Define database file path inside the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "finance.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables and seed initial default data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Categories table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            type TEXT NOT NULL
        );
    """)

    # Create Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT
        );
    """)

    conn.commit()

    # Seed Default Categories if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ("Gaji", "Pemasukan"),
            ("Freelance", "Pemasukan"),
            ("Uang kaget", "Pemasukan"),
            ("Makanan & Minuman", "Pengeluaran"),
            ("Transportasi", "Pengeluaran"),
            ("Belanja", "Pengeluaran"),
            ("Hiburan", "Pengeluaran"),
            ("Jajan", "Pengeluaran"),
            ("Tagihan", "Pengeluaran"),
            ("Kesehatan", "Pengeluaran"),
            ("Pendidikan", "Pengeluaran"),
            ("Investasi", "Pengeluaran")
        ]
        cursor.executemany(
            "INSERT INTO categories (category, type) VALUES (?, ?)",
            default_categories
        )
        conn.commit()

    # Seed Sample Transactions if empty (so app isn't blank on first run)
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        sample_transactions = [
            ("TRX001", "2026-09-20", "Pemasukan", "Gaji", 8500000.0, "Gaji Bulanan Sept 2026"),
            ("TRX002", "2026-09-21", "Pengeluaran", "Belanja", 450000.0, "Belanja mingguan pasar & dapur"),
            ("TRX003", "2026-09-21", "Pengeluaran", "Makanan & Minuman", 75000.0, "Makan siang & kopi"),
            ("TRX004", "2026-09-22", "Pengeluaran", "Transportasi", 150000.0, "Isi bensin mobil"),
            ("TRX005", "2026-09-22", "Pemasukan", "Freelance", 1200000.0, "Project landing page client")
        ]
        cursor.executemany(
            "INSERT INTO transactions (id, date, type, category, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
            sample_transactions
        )
        conn.commit()

    conn.close()


def get_transactions():
    """Fetch all transactions formatted as dictionary list."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date, type, category, amount, description FROM transactions ORDER BY date DESC, id DESC")
    rows = cursor.fetchall()
    conn.close()

    transactions = []
    for row in rows:
        transactions.append({
            "ID": row["id"],
            "Date": row["date"],
            "Type": row["type"],
            "Category": row["category"],
            "Amount": row["amount"],
            "Description": row["description"] or ""
        })
    return transactions


def get_next_transaction_id():
    """Generate next TRX id like TRX006."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM transactions ORDER BY ROWID DESC LIMIT 1")
    last_row = cursor.fetchone()
    conn.close()

    if last_row and last_row["id"].startswith("TRX"):
        try:
            num = int(last_row["id"].replace("TRX", ""))
            return f"TRX{num + 1:03d}"
        except ValueError:
            pass
    
    # Fallback if custom ID format or empty
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions")
    count = cursor.fetchone()[0]
    conn.close()
    return f"TRX{count + 1:03d}"


def add_transaction(transaction):
    """Insert a new transaction into database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    trx_id = transaction.get("id")
    if not trx_id:
        trx_id = get_next_transaction_id()

    cursor.execute("""
        INSERT INTO transactions (id, date, type, category, amount, description)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        trx_id,
        transaction["date"],
        transaction["type"],
        transaction["category"],
        float(transaction["amount"]),
        transaction.get("description", "")
    ))

    conn.commit()
    conn.close()


def update_transaction(transaction_id, transaction):
    """Update existing transaction by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE transactions
        SET date = ?, type = ?, category = ?, amount = ?, description = ?
        WHERE id = ?
    """, (
        transaction["date"],
        transaction["type"],
        transaction["category"],
        float(transaction["amount"]),
        transaction.get("description", ""),
        transaction_id
    ))

    conn.commit()
    conn.close()


def delete_transaction(transaction_id):
    """Delete a transaction by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    conn.close()


def get_categories():
    """Fetch all category records."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, type FROM categories ORDER BY type, category")
    rows = cursor.fetchall()
    conn.close()

    categories = []
    for row in rows:
        categories.append({
            "ID": row["id"],
            "Category": row["category"],
            "Type": row["type"]
        })
    return categories
