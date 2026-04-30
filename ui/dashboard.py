import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = "trading_bot.db"


def load_table(table_name, limit=50):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT {limit}",
        conn
    )
    conn.close()
    return df


def safe_load(table_name):
    try:
        return load_table(table_name)
    except Exception:
        return pd.DataFrame()


st.set_page_config(
    page_title="Trading Bot Dashboard",
    layout="wide"
)

st.title("Trading Bot Dashboard")

signals = safe_load("signals")
orders = safe_load("orders")
approvals = safe_load("approvals")
errors = safe_load("errors")

col1, col2, col3, col4 = st.columns(4)

col1.metric("최근 신호 수", len(signals))
col2.metric("최근 주문 수", len(orders))
col3.metric("승인/거절 기록", len(approvals))
col4.metric("에러 수", len(errors))

st.divider()

st.subheader("최근 신호")
if signals.empty:
    st.info("신호 데이터 없음")
else:
    st.dataframe(signals, width="stretch")

st.subheader("최근 주문")
if orders.empty:
    st.info("주문 데이터 없음")
else:
    st.dataframe(orders, width="stretch")

st.subheader("승인/거절 기록")
if approvals.empty:
    st.info("승인 데이터 없음")
else:
    st.dataframe(approvals, width="stretch")

st.subheader("에러 로그")
if errors.empty:
    st.success("에러 없음")
else:
    st.dataframe(errors, width="stretch")

st.divider()

st.caption("Trading Bot Dashboard - SQLite 기반 모니터링")