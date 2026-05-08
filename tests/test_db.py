from database.db import init_db
import sqlite3

init_db()

conn = sqlite3.connect("trading_bot.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM market_data LIMIT 5")

print(cursor.fetchall())

cursor.execute("SELECT * FROM investor_flow LIMIT 5")
print(cursor.fetchall())

conn.close()
