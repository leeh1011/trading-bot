import sqlite3

conn = sqlite3.connect("trading_bot.db")
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM market_data WHERE symbol='005930'")
print(cur.fetchone())

cur.execute("SELECT COUNT(*) FROM investor_flow WHERE symbol='005930'")
print(cur.fetchone())

conn.close()
exit()