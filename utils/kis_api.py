import requests
from settings import (
    KIS_APP_KEY,
    KIS_APP_SECRET,
    KIS_URL,
    KIS_ACCOUNT,
    KIS_ACCOUNT_PRODUCT,
)
import time
from database.db import log_error

class KISAPI:

    def __init__(self):
        self.access_token = None

    def get_token(self):
        if self.access_token:
            return self.access_token

        url = f"{KIS_URL}/oauth2/tokenP"

        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET
        }

        try:
            res = requests.post(url, headers=headers, json=body, timeout=10)
            data = res.json()

            if "access_token" not in data:
                log_error("KIS.get_token", str(data))
                print("❌ 토큰 발급 실패:", data)
                return None

            self.access_token = data["access_token"]
            print("✅ KIS 토큰 발급 성공")
            return self.access_token

        except Exception as e:
            log_error("KIS.get_token", str(e))
            print("❌ 토큰 요청 예외:", e)
            return None

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

        res = self._request_with_retry("GET", url, headers=headers, params=params)

        if res is None:
            return {"error": "request failed"}

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

        res = self._request_with_retry("GET", url, headers=headers, params=params)

        if res is None:
            return pd.DataFrame()

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
    
    def get_balance(self):
        """
        국내주식 잔고 조회
        모의투자 tr_id: VTTC8434R
        실전투자 tr_id: TTTC8434R
        """
        url = f"{KIS_URL}/uapi/domestic-stock/v1/trading/inquire-balance"

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": "VTTC8434R",
            "custtype": "P",
        }

        params = {
            "CANO": KIS_ACCOUNT,
            "ACNT_PRDT_CD": KIS_ACCOUNT_PRODUCT,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": "",
        }

        res = self._request_with_retry("GET", url, headers=headers, params=params)

        if res is None:
            return {"error": "request failed"}

        return res.json()
    
    def place_order(self, symbol, qty, side, price=0):
        """
        국내주식 모의투자 주문
        side: "BUY" or "SELL"
        price=0 이면 시장가
        """
        url = f"{KIS_URL}/uapi/domestic-stock/v1/trading/order-cash"

        if side == "BUY":
            tr_id = "VTTC0802U"
        elif side == "SELL":
            tr_id = "VTTC0801U"
        else:
            raise ValueError("side must be BUY or SELL")

        # 시장가: ORD_DVSN = "01", ORD_UNPR = "0"
        body = {
            "CANO": KIS_ACCOUNT,
            "ACNT_PRDT_CD": KIS_ACCOUNT_PRODUCT,
            "PDNO": symbol,
            "ORD_DVSN": "01",
            "ORD_QTY": str(int(qty)),
            "ORD_UNPR": str(int(price)),
        }

        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {self.access_token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": tr_id,
            "custtype": "P",
        }

        res = self._request_with_retry("GET", url, headers=headers, params=params)

        if res is None:
            return {"error": "request failed"}

        print("주문 status:", res.status_code)
        print("주문 text:", res.text)

        return res.json()
    
    def _request_with_retry(self, method, url, headers=None, params=None, json=None, retries=3):
        for attempt in range(1, retries + 1):
            try:
                if method == "GET":
                    res = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=10
                    )
                elif method == "POST":
                    res = requests.post(
                        url,
                        headers=headers,
                        json=json,
                        timeout=10
                    )
                else:
                    raise ValueError("method must be GET or POST")

                return res

            except Exception as e:
                log_error(
                    "KIS.request",
                    f"attempt={attempt}, error={e}"
                )
                print(f"⚠️ API 재시도 {attempt}/{retries}: {e}")
                time.sleep(1)

        return None