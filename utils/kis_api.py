import requests
from config import KIS_APP_KEY, KIS_APP_SECRET, KIS_URL


class KISAPI:

    def __init__(self):
        self.access_token = None

    def get_token(self):
        url = f"{KIS_URL}/oauth2/tokenP"

        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET
        }

        res = requests.post(url, headers=headers, json=body)
        data = res.json()

        print("토큰 응답:", data)  # 디버깅용

        self.access_token = data.get("access_token")

        return self.access_token

    def get_price(self, symbol):
        url = f"{KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "FHKST01010100"
        }

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol
        }

        res = requests.get(url, headers=headers, params=params)

        return res.json()
    
    def get_minute_chart(self, symbol, hour=None):
        """
        국내주식 당일 분봉 조회
        기본: 현재 시각 기준 최근 분봉 데이터
        """
        import datetime
        import pandas as pd

        if hour is None:
            hour = datetime.datetime.now().strftime("%H%M%S")

        url = f"{KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"

        headers = {
            "authorization": f"Bearer {self.access_token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "FHKST03010200"
        }

        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_HOUR_1": hour,
            "FID_PW_DATA_INCU_YN": "Y"
        }

        res = requests.get(url, headers=headers, params=params)
        data = res.json()

        if data.get("rt_cd") != "0":
            print("❌ 분봉 조회 실패:", data)
            return pd.DataFrame()

        rows = data.get("output2", [])

        candles = []
        for row in rows:
            candles.append({
                "time": row.get("stck_cntg_hour"),
                "open": float(row.get("stck_oprc", 0)),
                "high": float(row.get("stck_hgpr", 0)),
                "low": float(row.get("stck_lwpr", 0)),
                "close": float(row.get("stck_prpr", 0)),
                "volume": float(row.get("cntg_vol", 0)),
            })

        df = pd.DataFrame(candles)

        if df.empty:
            return df

        df = df.sort_values("time").reset_index(drop=True)
        return df