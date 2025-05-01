# File: src/data/loader.py

import os
import ccxt
import pandas as pd
from .parser import parse_ohlcv
from config import START_DATE, DATA_DIR

_exchange = ccxt.binance({
    "enableRateLimit": True,
    "options": {"fetchCurrencies": False},
})

def fetch_ohlcv(symbol: str, timeframe: str = "1h",
                limit: int = None, since: int = None) -> pd.DataFrame:
    """
    拉取 OHLCV，返回 DataFrame。
    """
    if since is None:
        since = _exchange.parse8601(f"{START_DATE}T00:00:00Z")
    bars = _exchange.fetch_ohlcv(symbol, timeframe,
                                 since=since, limit=limit)
    df = parse_ohlcv(bars)
    # 同时把 parquet 落到 DATA_DIR
    safe = symbol.replace("/", "_")
    path = DATA_DIR / f"{safe}_{timeframe}.parquet"
    os.makedirs(path.parent, exist_ok=True)
    df.to_parquet(path)
    return df

def fetch_and_save_csv(symbol: str, timeframe: str = "1h",
                       limit: int = None, since: int = None,
                       out_dir: str = ".") -> str:
    """
    拉取 OHLCV 并保存为 CSV。返回文件路径。
    """
    df = fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
    fn = f"{symbol.replace('/', '_')}_{timeframe}.csv"
    out = os.path.join(out_dir, fn)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    df.to_csv(out)
    return out
