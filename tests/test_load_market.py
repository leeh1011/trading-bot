from database.db import load_market_data

df = load_market_data("005930", limit=10)

print(df)