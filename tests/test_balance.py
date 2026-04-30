from utils.kis_api import KISAPI

api = KISAPI()

token = api.get_token()
print("TOKEN IS NONE?", token is None)
print("TOKEN PREVIEW:", str(token)[:20])

balance = api.get_balance()
print("BALANCE IS NONE?", balance is None)
print("BALANCE:", balance)