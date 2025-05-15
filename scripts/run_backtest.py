#!/usr/bin/env python3
"""
scripts/run_backtest.py

批量回测＋信号图 & 回测图，支持全仓/部分仓位配置，并附带绩效评估。
"""

import os
import sys
import argparse
import importlib
import inspect

import pandas as pd
import numpy as np
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

def plot_candle_signals(df_raw, df_ind, entry_times, exit_times, out_path):
    """
    df_raw, df_ind: 同一时间窗口的原始和指标DataFrame
    entry_times, exit_times: 时间戳列表
    out_path: 图片保存完整路径
    """
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

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
    if 'upper' in df_ind.columns and 'lower' in df_ind.columns and 'mid' in df_ind.columns:
        ax.plot(df_ind.index, df_ind['upper'], '--', label='Upper')
        ax.plot(df_ind.index, df_ind['mid'],   '-',  label='Mid')
        ax.plot(df_ind.index, df_ind['lower'], '--', label='Lower')
    elif 'ma' in df_ind.columns:
        ax.plot(df_ind.index, df_ind['ma'], '-', lw=2, label='MA')

    # 绘进出场
    if entry_times:
        lows = df_ind.loc[entry_times,'low'] * 0.995
        ax.scatter(entry_times, lows, s=100, c='red',   marker='o', label='Entry')
    if exit_times:
        highs= df_ind.loc[exit_times,'high'] * 1.005
        ax.scatter(exit_times, highs, s=100, c='grey', marker='o', label='Exit')

    ax.legend(loc='upper left'); ax.grid(True)

    # 绘成交量
    axv.bar(df_raw.index, df_raw['volume'], width=0.01)
    axv.grid(True)

    # 标题用文件名
    ax.set_title(os.path.basename(out_path).replace('_',' ').replace('.png',''))
    fig.autofmt_xdate()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()

def evaluate_performance(res: pd.DataFrame, period_hours: float) -> dict:
    """
    计算年化收益、年化波动、夏普比率和最大回撤。
    res 必须包含 equity 列，索引为 DatetimeIndex。
    period_hours: K 线周期对应的小时数，例如 4 表示 4h。
    """
    df = res.copy()
    df['ret'] = df['equity'].pct_change().fillna(0)
    ann_factor = 365 * 24 / period_hours

    # 累计收益
    cum_ret = df['equity'].iloc[-1] / df['equity'].iloc[0] - 1
    periods = len(df)
    ann_return = (1 + cum_ret) ** (ann_factor / periods) - 1

    # 年化波动率
    ann_vol = df['ret'].std() * np.sqrt(ann_factor)

    # 夏普比率（无风险利率假设为 0）
    sharpe = ann_return / ann_vol if ann_vol != 0 else np.nan

    # 最大回撤
    running_max = df['equity'].cummax()
    drawdown    = (df['equity'] - running_max) / running_max
    max_dd      = drawdown.min()

    return {
        "Annualized Return":     ann_return,
        "Annualized Volatility": ann_vol,
        "Sharpe Ratio":          sharpe,
        "Max Drawdown":          max_dd,
    }

def main():
    p = argparse.ArgumentParser(description="批量回测＋信号 & 回测图")
    p.add_argument("--mode",        choices=["plot","backtest"], default="plot")
    p.add_argument("--symbols",     required=True, help="逗号分隔交易对，如 BTC/USDT")
    p.add_argument("--timeframe",   default="4h",    help="K 线周期")
    p.add_argument("--limit",       type=int, default=300, help="拉取多少根 K 线")
    p.add_argument("--last_n",      type=int, default=200, help="画图取最后多少根（0=全部）")
    p.add_argument("--strategy",    required=True, choices=AVAILABLE.keys())
    p.add_argument("--children",    default="", help="follow_through 子策略 keys")
    p.add_argument("--comb_mode",   choices=["and","majority"], default="and")
    p.add_argument("--out_dir",     required=True, help="输出目录")
    p.add_argument("--window",      type=int,   default=30)
    p.add_argument("--mult",        type=float, default=2.0)
    p.add_argument("--period",      type=int,   default=15)
    p.add_argument("--stop_loss",   type=float, default=0.05)
    p.add_argument("--take_profit", type=float, default=0.10)
    p.add_argument("--trailing_ma", type=str,   default="ma")
    p.add_argument("--position_size", type=float, default=1.0,
                   help="建仓时使用的资金比例（0~1），1.0=全仓")
    args = p.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)
    init_kwargs = {'window':args.window,'mult':args.mult,'period':args.period}
    strat = get_strategy(args.strategy, args, init_kwargs)

    bt = None
    if args.mode == "backtest":
        tm = args.trailing_ma if args.strategy == "ma15_breakout" else None
        bt = Backtester(
            init_cash     = 1_000_000,
            stop_loss     = args.stop_loss,
            take_profit   = args.take_profit,
            trailing_ma   = tm,
            position_size = args.position_size
        )

    for sym in args.symbols.split(","):
        print(f"\n→ Processing {sym} [{args.mode}]")

        # 1) 拉全量数据
        df_full = fetch_ohlcv(sym, args.timeframe, limit=args.limit)

        # 2) 截取最后 last_n 根
        if args.last_n > 0:
            df_raw = df_full.iloc[-args.last_n:].copy()
        else:
            df_raw = df_full.copy()

        # 3) 在窗口上计算指标和信号
        df_ind = strat.compute(df_raw)
        entry_times, _ = strat.get_signal_layers(df_ind)
        exit_times     = strat.get_exit_layers(df_ind)

        # 4) 保存信号图
        safe_sym = sym.replace("/", "_")
        fn_sig = os.path.join(args.out_dir, f"{safe_sym}_signals.png")
        plot_candle_signals(df_raw, df_ind, entry_times, exit_times, fn_sig)
        print(fn_sig)

        # 5) backtest 模式下再画实际成交 & equity
        if args.mode == "backtest":
            res = bt.run(df_ind, entry_times, exit_times)

            # 回测成交图
            real_e = res.dropna(subset=['entry_price']).index.tolist()
            real_x = res.dropna(subset=['exit_price']).index.tolist()
            fn_bt = os.path.join(args.out_dir, f"{safe_sym}_backtest.png")
            plot_candle_signals(df_raw, df_ind, real_e, real_x, fn_bt)
            print(fn_bt)

            # equity CSV + PNG
            csv_eq = os.path.join(args.out_dir, f"{safe_sym}_equity.csv")
            res[['equity','drawdown']].to_csv(csv_eq)
            print(csv_eq)
            png_eq = csv_eq.replace('.csv','.png')
            plt.figure(figsize=(10,4))
            plt.plot(res.index, res['equity'], linewidth=2)
            plt.title(f"{sym} Equity Curve")
            plt.ylabel("Equity"); plt.grid(True)
            plt.tight_layout(); plt.savefig(png_eq, dpi=150); plt.close()
            print(png_eq)

            # 配对交易明细
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

            # 6) 绩效评估
            hours = float(args.timeframe.rstrip('h'))
            metrics = evaluate_performance(res, period_hours=hours)
            print("\n=== Performance Metrics ===")
            for name, val in metrics.items():
                print(f"{name:25s}: {val:.2%}")

if __name__=="__main__":
    main()
