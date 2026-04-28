import pandas as pd


def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    RSI 계산
    """
    delta = data["close"].diff()

    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def moving_average(data: pd.DataFrame, window: int = 20) -> pd.Series:
    """
    이동평균 계산
    """
    return data["close"].rolling(window=window).mean()
