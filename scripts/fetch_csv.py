#!/usr/bin/env python3
# File: scripts/fetch_csv.py

import os
import sys
import argparse

# 插入 src/ 到模块路径
sys.path.append(os.path.abspath(os.path.join(__file__, "..", "..", "src")))

from data.loader import fetch_and_save_csv

def main():
    p = argparse.ArgumentParser(description="批量拉取 OHLCV 到 CSV")
    p.add_argument("--symbols",  type=str, required=True,
                   help="逗号分隔交易对，如 BTC/USDT,ETH/USDT")
    p.add_argument("--timeframe",type=str, default="1h",
                   help="K 线周期，如 1h,4h,15m")
    p.add_argument("--limit",    type=int, default=None,
                   help="拉取多少根 K 线")
    p.add_argument("--since",    type=int, default=None,
                   help="起始时间戳（ms），优先于 limit")
    p.add_argument("--out_dir",  type=str, required=True,
                   help="CSV 保存目录")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    for s in args.symbols.split(","):
        path = fetch_and_save_csv(
            symbol   = s,
            timeframe= args.timeframe,
            limit    = args.limit,
            since    = args.since,
            out_dir  = args.out_dir
        )
        print(f"✅ Saved {s} → {path}")

if __name__ == "__main__":
    main()
