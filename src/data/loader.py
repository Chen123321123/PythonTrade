# File: src/data/loader.py

import os
import ccxt
import pandas as pd
from .parser import parse_ohlcv
from config import START_DATE, DATA_DIR, EXCHANGE  # 只导入这三项

# 取 config.PROXIES（如果存在），否则用空字典
import config as _cfg
_PROXY_SETTINGS = getattr(_cfg, "PROXIES", {})

# 动态创建 CCXT 交易所实例
# 例如 EXCHANGE="binance" or "kraken" or "coinbasepro"
_exchange = getattr(ccxt, EXCHANGE)(
    {
        "enableRateLimit": True,
        **(_PROXY_SETTINGS or {}),
    }
)

def fetch_ohlcv(symbol: str, timeframe: str = "1h",
                limit: int = None, since: int = None) -> pd.DataFrame:
    """
    拉取 OHLCV，返回 DataFrame 并缓存到 parquet。
    支持 BTC/USDT 和 BTC/USD 两种写法，自动映射成交易所支持的 BTC/USD。
    """
    if since is None:
        since = _exchange.parse8601(f"{START_DATE}T00:00:00Z")

    # 如果写了 /USDT，就替换成 /USD
    ex_symbol = symbol
    if ex_symbol.endswith("/USDT"):
        ex_symbol = ex_symbol.replace("/USDT", "/USD")

    bars = _exchange.fetch_ohlcv(ex_symbol, timeframe,
                                 since=since, limit=limit)
    df = parse_ohlcv(bars)

    # 缓存
    safe = symbol.replace("/", "_")
    path = DATA_DIR / f"{safe}_{timeframe}.parquet"
    os.makedirs(path.parent, exist_ok=True)
    df.to_parquet(path)
    return df

def fetch_and_save_csv(symbol: str, timeframe: str = "1h",
                       limit: int = None, since: int = None,
                       out_dir: str = ".") -> str:
    """
    拉取 OHLCV 并保存到 CSV，返回文件路径。
    """
    df = fetch_ohlcv(symbol, timeframe, limit=limit, since=since)
    fn = f"{symbol.replace('/', '_')}_{timeframe}.csv"
    out = os.path.join(out_dir, fn)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    df.to_csv(out)
    return out
