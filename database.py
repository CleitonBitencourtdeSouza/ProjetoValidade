import os
import sqlite3
from datetime import date, timedelta

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expiry_tracker.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            cost_price REAL NOT NULL,
            expiry_date TEXT NOT NULL DEFAULT '2100-01-01',
            status TEXT NOT NULL DEFAULT 'available',
            discarded_at TEXT
        )
        """
    )

    columns = conn.execute("PRAGMA table_info(products)").fetchall()
    if not any(column[1] == "expiry_date" for column in columns):
        conn.execute("ALTER TABLE products ADD COLUMN expiry_date TEXT NOT NULL DEFAULT '2100-01-01'")
    if not any(column[1] == "status" for column in columns):
        conn.execute("ALTER TABLE products ADD COLUMN status TEXT NOT NULL DEFAULT 'available'")
    if not any(column[1] == "discarded_at" for column in columns):
        conn.execute("ALTER TABLE products ADD COLUMN discarded_at TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_key TEXT NOT NULL,
            supplier TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            barcode TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            batch_number TEXT NOT NULL,
            expiry_date TEXT NOT NULL,
            status TEXT DEFAULT 'available',
            action_note TEXT,
            discarded_at TEXT,
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
        """
    )

    batch_columns = conn.execute("PRAGMA table_info(batches)").fetchall()
    if not any(column[1] == "discarded_at" for column in batch_columns):
        conn.execute("ALTER TABLE batches ADD COLUMN discarded_at TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS promotions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            batch_number TEXT,
            new_sale_price REAL NOT NULL,
            promotion_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
        """
    )

    conn.commit()
    conn.close()


def validate_nf_key(key: str) -> bool:
    if not key or len(key) != 44:
        return False
    return key.isdigit()


def get_alert_level(expiry_date: date) -> str:
    today = date.today()
    delta_days = (expiry_date - today).days

    if delta_days < 0:
        return "expired"
    if delta_days <= 7:
        return "critical"
    if delta_days <= 15:
        return "warning"
    if delta_days <= 30:
        return "attention"
    return "healthy"


def add_product(barcode: str, description: str, category: str, cost_price: float, expiry_date: str = "2100-01-01"):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO products (barcode, description, category, cost_price, expiry_date, status, discarded_at) VALUES (?, ?, ?, ?, ?, 'available', NULL)",
            (barcode, description, category, cost_price, expiry_date),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_products():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM products ORDER BY description").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_products_for_alerts():
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, barcode, description, category, expiry_date, status, discarded_at FROM products WHERE status NOT IN ('discarded', 'sold', 'promoted') ORDER BY expiry_date ASC"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def find_product_by_barcode(barcode: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_batch(invoice_key: str, supplier: str, entry_date: str, barcode: str, quantity: int, batch_number: str, expiry_date: str):
    if not validate_nf_key(invoice_key):
        raise ValueError("NF-e key must have 44 numeric digits.")

    product = find_product_by_barcode(barcode)
    if not product:
        raise ValueError("Product not found. Please register the product first.")

    conn = get_connection()
    conn.execute(
        "INSERT INTO batches (invoice_key, supplier, entry_date, barcode, quantity, batch_number, expiry_date, status) VALUES (?, ?, ?, ?, ?, ?, ?, 'available')",
        (invoice_key, supplier, entry_date, barcode, quantity, batch_number, expiry_date),
    )
    conn.commit()
    conn.close()

    if product.get("expiry_date"):
        try:
            db_expiry = date.fromisoformat(product["expiry_date"])
            batch_expiry = date.fromisoformat(expiry_date)
            if batch_expiry < db_expiry:
                conn = get_connection()
                conn.execute(
                    "UPDATE products SET expiry_date = ? WHERE barcode = ?",
                    (batch_expiry.isoformat(), barcode),
                )
                conn.commit()
                conn.close()
        except ValueError:
            pass


def get_batches_for_dashboard():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT b.id, b.invoice_key, b.supplier, b.entry_date, b.barcode, p.description, p.category,
               b.quantity, b.batch_number, b.expiry_date, b.status, b.action_note, b.discarded_at
        FROM batches b
        JOIN products p ON p.barcode = b.barcode
        WHERE b.status NOT IN ('discarded', 'sold', 'promoted')
        ORDER BY b.expiry_date ASC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_product_status(product_id: int, status: str, discarded_at: str = None):
    conn = get_connection()
    if status == "discarded":
        discarded_at = discarded_at or date.today().isoformat()
    else:
        discarded_at = None
    conn.execute(
        "UPDATE products SET status = ?, discarded_at = ? WHERE id = ?",
        (status, discarded_at, product_id),
    )
    conn.commit()
    conn.close()


def update_batch_status(batch_id: int, status: str, action_note: str = ""):
    conn = get_connection()
    discarded_at = date.today().isoformat() if status == "discarded" else None
    conn.execute(
        "UPDATE batches SET status = ?, action_note = ?, discarded_at = ? WHERE id = ?",
        (status, action_note, discarded_at, batch_id),
    )
    conn.commit()
    conn.close()


def get_loss_report(start_date: str, end_date: str):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT category, SUM(total_loss) AS total_loss, MIN(discard_date) AS discard_date
        FROM (
            SELECT p.category,
                   b.quantity * p.cost_price AS total_loss,
                   COALESCE(b.discarded_at, b.entry_date) AS discard_date
            FROM batches b
            JOIN products p ON p.barcode = b.barcode
            WHERE b.status = 'discarded'
              AND COALESCE(b.discarded_at, b.entry_date) BETWEEN ? AND ?

            UNION ALL

            SELECT p.category,
                   p.cost_price AS total_loss,
                   p.discarded_at AS discard_date
            FROM products p
            WHERE p.status = 'discarded'
              AND COALESCE(p.discarded_at, p.expiry_date) BETWEEN ? AND ?
        )
        GROUP BY category
        ORDER BY category ASC
        """,
        (start_date, end_date, start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_status_report(status: str, start_date: str, end_date: str):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, batch_number AS lot, barcode, description, category, expiry_date, status,
               COALESCE(discarded_at, expiry_date) AS reference_date,
               quantity, cost_price
        FROM (
            SELECT b.id, b.batch_number, b.barcode, p.description, p.category, b.expiry_date,
                   b.status, b.discarded_at, b.quantity, p.cost_price
            FROM batches b
            JOIN products p ON p.barcode = b.barcode
            WHERE b.status = ?
              AND COALESCE(b.discarded_at, b.entry_date) BETWEEN ? AND ?

            UNION ALL

            SELECT p.id, p.barcode AS batch_number, p.barcode, p.description, p.category,
                   p.expiry_date, p.status, p.discarded_at, 1 AS quantity, p.cost_price
            FROM products p
            WHERE p.status = ?
              AND COALESCE(p.discarded_at, p.expiry_date) BETWEEN ? AND ?
        )
        ORDER BY expiry_date ASC
        """,
        (status, start_date, end_date, status, start_date, end_date),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def add_promotion(barcode: str, batch_number: str, new_sale_price: float, promotion_date: str, notes: str = ""):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO promotions (barcode, batch_number, new_sale_price, promotion_date, notes) VALUES (?, ?, ?, ?, ?)",
            (barcode, batch_number, new_sale_price, promotion_date, notes),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_promotions():
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT p.id, p.barcode, pr.description, p.batch_number, p.new_sale_price, p.promotion_date, p.notes
        FROM promotions p
        JOIN products pr ON pr.barcode = p.barcode
        ORDER BY p.promotion_date DESC
        """
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
