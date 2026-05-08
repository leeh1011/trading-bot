import time
import requests
import datetime
import pandas as pd
import datetime

from settings import (
    KIS_APP_KEY,
    KIS_APP_SECRET,
    KIS_URL,
    KIS_ACCOUNT,
    KIS_ACCOUNT_PRODUCT,
    KIS_REAL_URL
)

from database.db import log_error


class KISAPI:
    def __init__(self):
        self.access_token = None
        self.token_expired_at = None
        self.last_request_time = 0

    def _rate_limit(self, min_interval=0.35):
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    def get_token(self):
        if self.access_token and self.token_expired_at:
            if datetime.datetime.now() < self.token_expired_at:
                return self.access_token

        url = f"{KIS_URL}/oauth2/tokenP"

        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
        }

        try:
            self._rate_limit(1.0)

            res = requests.post(url, headers=headers, json=body, timeout=10)
            data = res.json()

            if "access_token" not in data:
                log_error("KISAPI.get_token", str(data))
                print("토큰 발급 실패:", data)
                return None

            self.access_token = data["access_token"]

            expired_text = data.get("access_token_token_expired")
            if expired_text:
                self.token_expired_at = datetime.datetime.strptime(
                    expired_text,
                    "%Y-%m-%d %H:%M:%S"
                )
            else:
                self.token_expired_at = datetime.datetime.now() + datetime.timedelta(hours=23)

            print("KIS 토큰 발급 성공")
            return self.access_token

        except Exception as e:
            log_error("KISAPI.get_token", str(e))
            print("토큰 요청 예외:", e)
            return None

    def _headers(self, tr_id):
        token = self.get_token()

        return {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": KIS_APP_KEY,
            "appsecret": KIS_APP_SECRET,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _request_with_retry(self, method, url, headers=None, params=None, json=None, retries=3):
        for attempt in range(1, retries + 1):
            try:
                self._rate_limit()

                if method == "GET":
                    res = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=10,
                    )
                elif method == "POST":
                    res = requests.post(
                        url,
                        headers=headers,
                        json=json,
                        timeout=10,
                    )
                else:
                    raise ValueError("method must be GET or POST")

                data = res.json()

                # 토큰 만료/인증 문제 시 1회 재발급
                if data.get("msg_cd") in ["EGW00123", "EGW00121"]:
                    self.access_token = None
                    headers["authorization"] = f"Bearer {self.get_token()}"

                    if method == "GET":
                        res = requests.get(url, headers=headers, params=params, timeout=10)
                    else:
                        res = requests.post(url, headers=headers, json=json, timeout=10)

                return res

            except Exception as e:
                log_error(
                    "KISAPI._request_with_retry",
                    f"attempt={attempt}, error={e}"
                )
                print(f"API 재시도 {attempt}/{retries}: {e}")
                time.sleep(1)

        return None

    def get_price(self, symbol):
        url = f"{KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-price"

        headers = self._headers("FHKST01010100")

        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": symbol,
        }

        res = self._request_with_retry(
            "GET",
            url,
            headers=headers,
            params=params,
        )

        if res is None:
            return {"error": "price request failed"}

        return res.json()

    def get_minute_chart(self, symbol, hour=None):
        if hour is None:
            hour = datetime.datetime.now().strftime("%H%M%S")

        url = f"{KIS_URL}/uapi/domestic-stock/v1/quotations/inquire-time-itemchartprice"

        headers = self._headers("FHKST03010200")

        params = {
            "FID_ETC_CLS_CODE": "",
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_HOUR_1": hour,
            "FID_PW_DATA_INCU_YN": "Y",
        }

        res = self._request_with_retry(
            "GET",
            url,
            headers=headers,
            params=params,
        )

        if res is None:
            log_error("KISAPI.get_minute_chart", f"{symbol} request failed")
            return pd.DataFrame()

        try:
            data = res.json()

            if data.get("rt_cd") != "0":
                log_error("KISAPI.get_minute_chart", str(data))
                print("분봉 조회 실패:", data)
                return pd.DataFrame()

            rows = data.get("output2", [])
            candles = []

            for row in rows:
                candles.append({
                    "time": row.get("stck_cntg_hour"),
                    "open": float(row.get("stck_oprc", 0) or 0),
                    "high": float(row.get("stck_hgpr", 0) or 0),
                    "low": float(row.get("stck_lwpr", 0) or 0),
                    "close": float(row.get("stck_prpr", 0) or 0),
                    "volume": float(row.get("cntg_vol", 0) or 0),
                })

            df = pd.DataFrame(candles)

            if df.empty:
                return df

            return df.sort_values("time").reset_index(drop=True)

        except Exception as e:
            log_error("KISAPI.get_minute_chart", str(e))
            return pd.DataFrame()

    def get_balance(self):
        url = f"{KIS_URL}/uapi/domestic-stock/v1/trading/inquire-balance"

        headers = self._headers("VTTC8434R")

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

        res = self._request_with_retry(
            "GET",
            url,
            headers=headers,
            params=params,
        )

        if res is None:
            return {"error": "balance request failed"}

        return res.json()

    def place_order(self, symbol, qty, side="BUY", price=0):
        url = f"{KIS_URL}/uapi/domestic-stock/v1/trading/order-cash"

        if side == "BUY":
            tr_id = "VTTC0802U"
        elif side == "SELL":
            tr_id = "VTTC0801U"
        else:
            return {"error": "side must be BUY or SELL"}

        headers = self._headers(tr_id)

        body = {
            "CANO": KIS_ACCOUNT,
            "ACNT_PRDT_CD": KIS_ACCOUNT_PRODUCT,
            "PDNO": symbol,
            "ORD_DVSN": "01",
            "ORD_QTY": str(int(qty)),
            "ORD_UNPR": str(int(price)),
        }

        res = self._request_with_retry(
            "POST",
            url,
            headers=headers,
            json=body,
        )

        if res is None:
            return {"error": "order request failed"}

        return res.json()
    
    def get_investor_flow(self, symbol):
        url = f"{KIS_REAL_URL}/uapi/domestic-stock/v1/quotations/investor-trend-estimate"

        headers = self._headers("HHPTJ04160200")

        params = {
            "MKSC_SHRN_ISCD": symbol
        }

        res = self._request_with_retry(
            "GET",
            url,
            headers=headers,
            params=params,
        )

        if res is None:
            return None

        try:
            data = res.json()

            if data.get("rt_cd") != "0":
                log_error("KISAPI.get_investor_flow", str(data))
                print("외인/기관 조회 실패:", data)
                return None

            rows = data.get("output2", [])

            if not rows:
                return None

            latest = rows[0]

            foreign_net = int(latest.get("frgn_fake_ntby_qty", 0) or 0)
            institution_net = int(latest.get("orgn_fake_ntby_qty", 0) or 0)

            return {
                "datetime": str(datetime.datetime.now()),

                # 이 API는 순매수 추정 수량만 제공
                "foreign_buy": 0,
                "foreign_sell": 0,
                "foreign_net": foreign_net,

                "institution_buy": 0,
                "institution_sell": 0,
                "institution_net": institution_net,
            }

        except Exception as e:
            log_error("KISAPI.get_investor_flow", str(e))
            print("외인/기관 파싱 오류:", e)
            return None