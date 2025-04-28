# File: pythontrade/src/data/loader_equities.py

import yfinance as yf
from src.config import PROJECT_ROOT, DATA_DIR
import pandas as pd

def fetch_stock_ohlcv(symbol: str, period: str = "1y", interval: str = "1d"):
    """
    拉取美股日线数据，symbol 格式如 "AAPL"、"MSFT"。
      - period: 拉取多久的数据，比如 "6mo","1y","5y"
      - interval: 数据间隔，比如 "1d","1wk","1mo"
    """
    # 1. 用 yfinance 下载
    ticker = yf.Ticker(symbol)
    df = ticker.history(period=period, interval=interval)

    # 2. 重命名列，保持和 crypto OHLCV 一致
    df = df.rename(columns={
        "Open":  "open",
        "High":  "high",
        "Low":   "low",
        "Close": "close",
        "Volume":"volume"
    })
    df.index.name = "timestamp"

    # 3. 落盘
    safe_symbol = symbol.replace("/", "_")
    filename    = f"{safe_symbol}_stock_{interval}.parquet"
    path        = DATA_DIR / filename
    df.to_parquet(path)

    return df
