import sqlite3
from datetime import datetime

DB_PATH = "trading_bot.db"


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    create_market_data_table(conn)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        symbol TEXT,
        action TEXT,
        price REAL,
        reason TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        symbol TEXT,
        action TEXT,
        qty INTEGER,
        price REAL,
        status TEXT,
        raw_response TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        order_id TEXT,
        symbol TEXT,
        action TEXT,
        decision TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS errors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT,
        location TEXT,
        message TEXT
    )
    """)

    conn.commit()
    conn.close()


def log_signal(signal):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO signals (created_at, symbol, action, price, reason)
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        signal.get("symbol"),
        signal.get("action"),
        signal.get("price"),
        signal.get("reason"),
    ))

    conn.commit()
    conn.close()


def log_order(symbol, action, qty, price, status, raw_response):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO orders (created_at, symbol, action, qty, price, status, raw_response)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        symbol,
        action,
        qty,
        price,
        status,
        str(raw_response),
    ))

    conn.commit()
    conn.close()


def log_approval(order_id, symbol, action, decision):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO approvals (created_at, order_id, symbol, action, decision)
    VALUES (?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        order_id,
        symbol,
        action,
        decision,
    ))

    conn.commit()
    conn.close()


def log_error(location, message):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO errors (created_at, location, message)
    VALUES (?, ?, ?)
    """, (
        datetime.now().isoformat(),
        location,
        message,
    ))

    conn.commit()
    conn.close()

def create_market_data_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS market_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        datetime TEXT,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        volume REAL
    )
    """)

    conn.commit()

def save_market_data(symbol, row):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO market_data (
        symbol,
        datetime,
        open,
        high,
        low,
        close,
        volume
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        str(row.name),
        float(row["open"]),
        float(row["high"]),
        float(row["low"]),
        float(row["close"]),
        float(row["volume"])
    ))

    conn.commit()
    conn.close()