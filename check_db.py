import sqlite3

DB_NAME = "trading_bot.db"

conn = sqlite3.connect(DB_NAME)
cur = conn.cursor()

print("===== DB 테이블 목록 =====")
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [row[0] for row in cur.fetchall()]

for table in tables:
    print("-", table)

print()

# 5분봉 테이블 이름 후보
target_table = "market_data"

if target_table not in tables:
    print(f"'{target_table}' 테이블이 없습니다.")
    print("위 테이블 목록에서 5분봉 데이터 테이블 이름을 확인하세요.")
    conn.close()
    exit()

print(f"===== {target_table} 컬럼 목록 =====")
cur.execute(f"PRAGMA table_info({target_table});")
columns = cur.fetchall()

column_names = []

for col in columns:
    column_names.append(col[1])
    print(col)

print()

print(f"===== {target_table} 전체 개수 =====")
cur.execute(f"SELECT COUNT(*) FROM {target_table};")
print("전체 rows:", cur.fetchone()[0])

print()

if "symbol" in column_names:
    print("===== 종목별 데이터 개수 =====")
    cur.execute(f"""
    SELECT symbol, COUNT(*)
    FROM {target_table}
    GROUP BY symbol
    ORDER BY symbol;
    """)

    for symbol, count in cur.fetchall():
        print(symbol, count)

    print()

# 시간 컬럼 자동 탐색
time_column = None
for candidate in ["datetime", "timestamp", "date", "time", "created_at"]:
    if candidate in column_names:
        time_column = candidate
        break

if "symbol" in column_names and time_column is not None:
    print("===== 종목별 최근 데이터 시간 =====")
    cur.execute(f"""
    SELECT symbol, MAX({time_column})
    FROM {target_table}
    GROUP BY symbol
    ORDER BY symbol;
    """)

    for symbol, last_time in cur.fetchall():
        print(symbol, last_time)

    print()

    print("===== 최근 데이터 10개 =====")
    cur.execute(f"""
    SELECT *
    FROM {target_table}
    ORDER BY {time_column} DESC
    LIMIT 10;
    """)

    for row in cur.fetchall():
        print(row)
else:
    print("symbol 컬럼 또는 시간 컬럼을 찾지 못했습니다.")
    print("시간 컬럼 후보: datetime, timestamp, date, time, created_at")

conn.close()