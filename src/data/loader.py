# File: pythontrade/src/data/loader.py

import ccxt
from .parser import parse_ohlcv
from src.config import START_DATE, DATA_DIR

def fetch_ohlcv(symbol: str, timeframe: str = "1h"):
    """
    拉取指定交易对的 OHLCV（K 线）数据，解析成 DataFrame，
    并以 <symbol>_<timeframe>.parquet 的格式落盘到 DATA_DIR。
    """
    # 1. 初始化交易所实例，只拿公共行情，不带任何身份验证
    ex = ccxt.binance({
        "enableRateLimit": True,
        # 禁止自动拉私有接口，加快初始化
        "options": {"fetchCurrencies": False},
    })

    # 2. 转换起始时间，并拉数据
    since = ex.parse8601(f"{START_DATE}T00:00:00Z")
    raw   = ex.fetch_ohlcv(symbol, timeframe, since=since)

    # 3. 解析成 DataFrame
    df = parse_ohlcv(raw)

    # 4. 生成合法文件名，写入 parquet
    safe_symbol = symbol.replace("/", "_")
    path = DATA_DIR / f"{safe_symbol}_{timeframe}.parquet"
    df.to_parquet(path)

    return df
