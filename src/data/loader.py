# src/data/loader.py

import os
import ccxt
import pandas as pd
from .parser import parse_ohlcv
from config import START_DATE, DATA_DIR, EXCHANGE
import config as _cfg

# 取 config.PROXIES（如果存在），否则用空字典
_PROXY_SETTINGS = getattr(_cfg, "PROXIES", {})

# 动态创建 CCXT 交易所实例
_exchange = getattr(ccxt, EXCHANGE)(
    {
        "enableRateLimit": True,
        **(_PROXY_SETTINGS or {}),
    }
)


def fetch_ohlcv(symbol: str,
                timeframe: str = "1h",
                limit: int = None,
                since: int = None) -> pd.DataFrame:
    """
    拉取 OHLCV，返回按时间升序排序的 DataFrame 并缓存到 parquet。
    如果只给了 limit 而未给 since，则默认从“现在”往回取最近 limit 条。
    只有在 since 明确传入或 limit 也为 None 时，才会从 START_DATE 开始取所有数据。
    """
    # 决定 real_since 参数
    if since is None and limit is not None:
        # 只指定 limit：不要给 since，让 CCXT 拿最新的 limit 条
        real_since = None
    else:
        # either since 已传，或两者都没传，则从 START_DATE 开始拉
        real_since = _exchange.parse8601(f"{START_DATE}T00:00:00Z")

    # 兼容 /USDT 到 /USD
    ex_symbol = symbol
    if ex_symbol.endswith("/USDT"):
        ex_symbol = ex_symbol.replace("/USDT", "/USD")

    # 拉数据
    bars = _exchange.fetch_ohlcv(
        ex_symbol,
        timeframe,
        since=real_since,
        limit=limit
    )
    df = parse_ohlcv(bars)

    # 强制按时间升序
    df.sort_index(inplace=True)

    # 缓存到 parquet
    safe = symbol.replace("/", "_")
    path = DATA_DIR / f"{safe}_{timeframe}.parquet"
    os.makedirs(path.parent, exist_ok=True)
    df.to_parquet(path)

    return df
