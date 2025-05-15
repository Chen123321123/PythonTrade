# src/backend/core.py

import os, time, importlib, inspect
import pandas as pd, numpy as np
import matplotlib


matplotlib.use("Agg")
               
import matplotlib.pyplot as plt, matplotlib.dates as mdates

from data.loader     import fetch_ohlcv
from backtest.engine import Backtester

AVAILABLE = {
    "bollinger_narrow": "strategies.bollinger_narrow:BollingerNarrowStrategy",
    "ma15_breakout":    "strategies.ma15_breakout:MA15BreakoutStrategy",
    "follow_through":   "strategies.follow_through:CombinedFollowThroughStrategy",
}

def get_strategy(name: str, params: dict):
    """
    从 params 里读取初始化参数，动态实例化策略。
    params 中应包含：
      - window, mult, period
      - children（可选）, comb_mode（可选）
    """
    # 1) 找到策略类路径
    mod_path, cls_name = AVAILABLE[name].split(":")
    mod = importlib.import_module(mod_path)
    cls = getattr(mod, cls_name)

    # 2) 从 params 构造 init_kwargs
    init_kwargs = {
        "window": params["window"],
        "mult":   params["mult"],
        "period": params["period"],
    }

    # 3) 处理 follow_through 的子策略逻辑
    if name == "follow_through":
        children_keys = [k for k in params.get("children", "").split(",") if k]
        specs = [AVAILABLE[k] for k in children_keys]
        return cls(children=specs,
                   mode=params.get("comb_mode", "and"),
                   init_kwargs=init_kwargs)

    # 4) 其余策略：只传 __init__ 中真正需要的参数
    sig = inspect.signature(cls.__init__)
    filtered = {
        k: init_kwargs[k]
        for k in sig.parameters
        if k != "self" and k in init_kwargs
    }
    return cls(**filtered)

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

def run_backtest_api(params: dict) -> dict:
    """
    接收参数字典 params，执行信号绘制和回测，并返回结构化结果：
      - run_id    : 本次任务唯一 ID
      - out_dir   : 本次输出根目录
      - results   : 每个 symbol 对应的文件路径和绩效数据
    必需的 params 字段：
      mode, symbols, timeframe, limit, last_n,
      strategy, children, comb_mode,
      window, mult, period,
      stop_loss, take_profit, trailing_ma,
      position_size, out_dir
    """
    # 1) 准备 run_id 和输出目录
    run_id  = f"{params['strategy']}_{int(time.time())}"
    base    = params['out_dir']
    out_dir = os.path.join(base, run_id)
    os.makedirs(out_dir, exist_ok=True)

    # 2) 策略实例化
    strat = get_strategy(params['strategy'], params)

    # 3) Backtester（如果是 backtest 模式）
    bt = None
    if params.get('mode') == 'backtest':
        tm = params.get('trailing_ma') if params['strategy'] == 'ma15_breakout' else None
        bt = Backtester(
            init_cash     = params.get('init_cash', 1_000_000),
            stop_loss     = params['stop_loss'],
            take_profit   = params['take_profit'],
            trailing_ma   = tm,
            position_size = params['position_size'],
        )

    # 4) 遍历每个 symbol，执行流程
    results = {}
    for sym in params['symbols'].split(','):
        # 4.1) 拉数据 & 截取最后 N 根
        df_full = fetch_ohlcv(sym, params['timeframe'], limit=params['limit'])
        if params['last_n'] > 0:
            df_raw = df_full.iloc[-params['last_n']:].copy()
        else:
            df_raw = df_full.copy()

        # 4.2) 计算指标和信号
        df_ind        = strat.compute(df_raw)
        entry_times, _ = strat.get_signal_layers(df_ind)
        exit_times     = strat.get_exit_layers(df_ind)

        # 4.3) 绘制并保存信号图
        safe     = sym.replace('/', '_')
        sig_path = os.path.join(out_dir, f"{safe}_signals.png")
        plot_candle_signals(df_raw, df_ind, entry_times, exit_times, sig_path)

        info = {'signals': sig_path}

        # 4.4) 如果是回测模式，再执行回测流程
        if bt:
            # 4.4.1) 运行回测引擎
            res = bt.run(df_ind, entry_times, exit_times)

            # 4.4.2) 保存回测成交图
            bt_path = os.path.join(out_dir, f"{safe}_backtest.png")
            plot_candle_signals(
                df_raw, df_ind,
                res.dropna(subset=['entry_price']).index.tolist(),
                res.dropna(subset=['exit_price']).index.tolist(),
                bt_path
            )
            info['backtest'] = bt_path

            # 4.4.3) 保存 equity CSV + PNG
            csv_eq = os.path.join(out_dir, f"{safe}_equity.csv")
            res[['equity', 'drawdown']].to_csv(csv_eq, index=True)
            png_eq = csv_eq.replace('.csv', '.png')
            plt.figure(figsize=(10, 4))
            plt.plot(res.index, res['equity'], linewidth=2)
            plt.tight_layout()
            plt.savefig(png_eq, dpi=150)
            plt.close()
            info['equity_csv'] = csv_eq
            info['equity_png'] = png_eq

            # 4.4.4) 绩效评估
            hours = float(params['timeframe'].rstrip('h'))
            perf  = evaluate_performance(res, period_hours=hours)
            info['performance'] = perf

        # 4.5) 收集单个 symbol 的结果
        results[sym] = info

    # 5) 返回最终结果
    return {
        'run_id':  run_id,
        'out_dir': out_dir,
        'results': results
    }

