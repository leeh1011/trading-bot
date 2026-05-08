from database.db import load_investor_flow

df = load_investor_flow("005930", limit=10)

print(df)