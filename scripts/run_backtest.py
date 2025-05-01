#!/usr/bin/env python3
"""
scripts/run_backtest.py

批量回测＋信号图 & 回测图，支持全仓/部分仓位配置。
"""

import os
import sys
import argparse
import importlib
import inspect

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# 1) 加载 src 到模块路径
SCRIPT_DIR   = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
SRC_ROOT     = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_ROOT)

from data.loader     import fetch_ohlcv
from backtest.engine import Backtester

# 策略映射
AVAILABLE = {
    "bollinger_narrow": "strategies.bollinger_narrow:BollingerNarrowStrategy",
    "ma15_breakout":    "strategies.ma15_breakout:MA15BreakoutStrategy",
    "follow_through":   "strategies.follow_through:CombinedFollowThroughStrategy",
}

def get_strategy(name, args, init_kwargs):
    mod_path, cls_name = AVAILABLE[name].split(":")
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)
    if name == "follow_through":
        keys  = [k for k in args.children.split(",") if k]
        specs = [AVAILABLE[k] for k in keys]
        return cls(children=specs, mode=args.comb_mode, init_kwargs=init_kwargs)
    sig = inspect.signature(cls.__init__)
    kw  = {k: init_kwargs[k] for k in sig.parameters if k!="self" and k in init_kwargs}
    return cls(**kw)

def plot_candle_signals(df_raw, df_ind, entry_times, exit_times, title, out_path):
    dates = mdates.date2num(df_raw.index.to_pydatetime())
    fig, (ax, axv) = plt.subplots(2,1, figsize=(14,8), sharex=True,
                                  gridspec_kw={'height_ratios':[3,1]})
    # 绘 K 线
    for i, row in enumerate(df_raw.itertuples()):
        o,h,l,c = row.open, row.high, row.low, row.close
        col = 'green' if c>=o else 'red'
        ax.vlines(dates[i], l, h, color=col, linewidth=1)
        ax.add_line(plt.Line2D([dates[i]]*2, [o,c], color=col, linewidth=4))
    # 绘指标
    if 'upper' in df_ind.columns:
        ax.plot(df_ind.index, df_ind['upper'], '--', label='Upper')
        ax.plot(df_ind.index, df_ind['mid'],   '-',  label='Mid')
        ax.plot(df_ind.index, df_ind['lower'], '--', label='Lower')
    if 'ma' in df_ind.columns:
        period = df_ind['ma'].attrs.get('period','')
        ax.plot(df_ind.index, df_ind['ma'], '-', lw=2, label=f"MA{period}")
    # 绘进出场
    if entry_times:
        lows = df_ind.loc[entry_times,'low'] * 0.995
        ax.scatter(entry_times, lows, s=100, c='red',   marker='o', label='Entry')
    if exit_times:
        highs= df_ind.loc[exit_times,'high'] * 1.005
        ax.scatter(exit_times, highs, s=100, c='grey', marker='o', label='Exit')
    ax.legend(loc='upper left'); ax.grid(True)
    # 绘成交量
    axv.bar(df_raw.index, df_raw['volume'], width=0.01); axv.grid(True)
    ax.set_title(title)
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def main():
    p = argparse.ArgumentParser(description="批量回测＋信号 & 回测图")
    p.add_argument("--mode",          choices=["plot","backtest"], default="plot")
    p.add_argument("--symbols",       required=True, help="逗号分隔交易对")
    p.add_argument("--timeframe",     default="4h",    help="K 线周期")
    p.add_argument("--limit",         type=int, default=300, help="拉取多少根 K 线")
    p.add_argument("--last_n",        type=int, default=200, help="画图取最后多少根（0=全部）")
    p.add_argument("--strategy",      required=True, choices=AVAILABLE.keys())
    p.add_argument("--children",      default="", help="follow_through 子策略 keys")
    p.add_argument("--comb_mode",     choices=["and","majority"], default="and")
    p.add_argument("--out_dir",       required=True, help="输出目录")
    p.add_argument("--window",        type=int,   default=30)
    p.add_argument("--mult",          type=float, default=2.0)
    p.add_argument("--period",        type=int,   default=15)
    p.add_argument("--stop_loss",     type=float, default=0.05)
    p.add_argument("--take_profit",   type=float, default=0.10)
    p.add_argument("--trailing_ma",   type=str,   default="ma")
    p.add_argument("--position_size", type=float, default=1.0,
                   help="建仓时使用的资金比例（0~1），1.0=全仓")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    init_kwargs = {'window':args.window,'mult':args.mult,'period':args.period}
    strat = get_strategy(args.strategy, args, init_kwargs)

    bt = None
    if args.mode=="backtest":
        tm = args.trailing_ma if args.strategy=="ma15_breakout" else None
        bt = Backtester(
            init_cash     = 1_000_000,
            stop_loss     = args.stop_loss,
            take_profit   = args.take_profit,
            trailing_ma   = tm,
            position_size = args.position_size
        )

    for sym in args.symbols.split(","):
        print(f"\n→ Processing {sym} [{args.mode}]")
        df  = fetch_ohlcv(sym, args.timeframe, limit=args.limit)
        df2 = strat.compute(df)

        entry_all, _ = strat.get_signal_layers(df2)
        exit_all     = strat.get_exit_layers(df2)

        # 根据 last_n 切出画图窗口
        df_raw = df.iloc[-args.last_n:].copy() if args.last_n>0 else df.copy()
        df_ind = df2.iloc[-args.last_n:].copy() if args.last_n>0 else df2.copy()

        # 交集，得到落在绘图区间内的时间戳
        entry_times = [t for t in entry_all if t in df_ind.index]
        exit_times  = [t for t in exit_all  if t in df_ind.index]

        # 1) signal 图
        fn_sig = os.path.join(args.out_dir, f"{sym.replace('/','_')}_signals.png")
        plot_candle_signals(df_raw, df_ind,
                            entry_times, exit_times,
                            f"{sym} Entry/Exit Signals",
                            fn_sig)
        print("✅", fn_sig)

        # 2) backtest 模式下再画实际成交 & equity
        if args.mode=="backtest":
            # 回测：直接传带时间戳的 df_ind 和 时间戳列表
            res = bt.run(df_ind, entry_times, exit_times)

            # 从结果提取真实成交的时间戳
            real_e = res.dropna(subset=['entry_price']).index.tolist()
            real_x = res.dropna(subset=['exit_price']).index.tolist()

            # backtest 图
            fn_bt = os.path.join(args.out_dir, f"{sym.replace('/','_')}_backtest.png")
            plot_candle_signals(df_raw, df_ind,
                                real_e, real_x,
                                f"{sym} Backtest Entry/Exit",
                                fn_bt)
            print("✅", fn_bt)

            # equity CSV + PNG
            csv_eq = os.path.join(args.out_dir, f"{sym.replace('/','_')}_equity.csv")
            res[['equity','drawdown']].to_csv(csv_eq)
            print("📈", csv_eq)
            png_eq = csv_eq.replace('.csv','.png')
            plt.figure(figsize=(10,4))
            plt.plot(res.index, res['equity'], linewidth=2)
            plt.title(f"{sym} Equity Curve")
            plt.ylabel("Equity"); plt.grid(True)
            plt.tight_layout(); plt.savefig(png_eq, dpi=150); plt.close()
            print("✅", png_eq)

            # 交易明细
            trades, cur = [], None
            for ts,row in res.iterrows():
                if pd.notna(row.entry_price):
                    cur = {'entry_time':ts, 'entry_price':row.entry_price}
                if pd.notna(row.exit_price) and cur:
                    cur.update({
                        'exit_time': ts,
                        'exit_price': row.exit_price,
                        'pnl':       row.exit_price - cur['entry_price']
                    })
                    trades.append(cur)
                    cur = None
            print("\n=== Paired Trades ===")
            print(pd.DataFrame(trades).to_string(index=False))

if __name__=="__main__":
    main()
