import sqlite3
import os
import pandas as pd
from datetime import datetime

DB_NAME = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "trading_bot.db"
)


def get_conn():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    create_market_data_table(conn)
    create_investor_flow_table(conn)
    create_backtest_table(conn)

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

def create_investor_flow_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS investor_flow (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        datetime TEXT,

        foreign_buy REAL,
        foreign_sell REAL,
        foreign_net REAL,

        institution_buy REAL,
        institution_sell REAL,
        institution_net REAL
    )
    """)

    conn.commit()

def save_investor_flow(symbol, flow):
    print("SAVING FLOW:", symbol, flow)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO investor_flow (
        symbol,
        datetime,

        foreign_buy,
        foreign_sell,
        foreign_net,

        institution_buy,
        institution_sell,
        institution_net
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        symbol,
        flow["datetime"],

        flow["foreign_buy"],
        flow["foreign_sell"],
        flow["foreign_net"],

        flow["institution_buy"],
        flow["institution_sell"],
        flow["institution_net"]
    ))

    conn.commit()
    conn.close()

def load_market_data(symbol, limit=200):
    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        datetime,
        open,
        high,
        low,
        close,
        volume
    FROM market_data
    WHERE symbol = ?
    ORDER BY id DESC
    LIMIT ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(symbol, limit)
    )

    conn.close()

    if df.empty:
        return df

    df = df.sort_values("datetime").reset_index(drop=True)

    numeric_cols = ["open", "high", "low", "close", "volume"]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])

    return df

def load_investor_flow(symbol, limit=200):
    conn = sqlite3.connect(DB_NAME)

    query = """
    SELECT
        datetime,
        foreign_buy,
        foreign_sell,
        foreign_net,
        institution_buy,
        institution_sell,
        institution_net
    FROM investor_flow
    WHERE symbol = ?
    ORDER BY id DESC
    LIMIT ?
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(symbol, limit)
    )

    conn.close()

    if df.empty:
        return df

    df = df.sort_values("datetime").reset_index(drop=True)

    numeric_cols = [
        "foreign_buy",
        "foreign_sell",
        "foreign_net",
        "institution_buy",
        "institution_sell",
        "institution_net",
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col])

    return df

def create_backtest_table(conn):
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS backtest_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        created_at TEXT,

        strategy TEXT,
        symbol TEXT,

        initial_cash REAL,
        final_cash REAL,

        total_profit REAL,
        total_return REAL,

        trade_count INTEGER,
        completed_trade_count INTEGER,

        win_count INTEGER,
        win_rate REAL
    )
    """)

    conn.commit()

def save_backtest_result(result, symbol):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO backtest_results (
        created_at,
        strategy,
        symbol,
        initial_cash,
        final_cash,
        total_profit,
        total_return,
        trade_count,
        completed_trade_count,
        win_count,
        win_rate
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),

        result.get("strategy"),
        symbol,

        result.get("initial_cash"),
        result.get("final_cash"),

        result.get("total_profit"),
        result.get("total_return"),

        result.get("trade_count"),
        result.get("completed_trade_count"),

        result.get("win_count"),
        result.get("win_rate"),
    ))

    conn.commit()
    conn.close()