import os
import mplfinance as mpf
import pandas as pd
from typing import List
import matplotlib.pyplot as plt

def plot_strategy(
    df: pd.DataFrame,
    signal_pts: List[pd.Timestamp],
    breakout_pts: List[pd.Timestamp],
    add_main: List,        # list of mpf.make_addplot already aligned to df
    out_path: str,
    title: str = None,
    style: str = "charles",
    volume: bool = True,
    figsize: tuple = (12, 6),
    last_n: int = None,    # if set, only plot the last `last_n` bars
    narrow_marker: str = "o",
    breakout_marker: str = "^",
    narrow_color: str = "blue",
    breakout_color: str = "red",
):
    """
    通用策略绘图函数。
    - df:         DataFrame，必须包含 open, high, low, close, volume
    - add_main:   list of mpf.make_addplot objects, 已与 df 对齐
    - signal_pts/breakout_pts: lists of Timestamp，标注在 df.index 上
    - last_n:     如果不为 None，则先截取 df.tail(last_n) 再画图
    """
    # 1. 切出最后 last_n 根
    if last_n is not None and last_n < len(df):
        df_plot = df.iloc[-last_n:].copy()
    else:
        df_plot = df.copy()

    # 2. 过滤信号点，只保留在 df_plot.index 上的
    pts = [ts for ts in signal_pts   if ts in df_plot.index]
    brs = [ts for ts in breakout_pts if ts in df_plot.index]

    # 3. 准备 addplot 列表（调用方已确保 add_main 与 df_plot 对齐）
    addplots = list(add_main)
    if pts:
        addplots.append(
            mpf.make_addplot(
                df_plot['close'].where(df_plot.index.isin(pts)),
                type='scatter',
                marker=narrow_marker,
                markersize=80,
                color=narrow_color,
            )
        )
    if brs:
        addplots.append(
            mpf.make_addplot(
                df_plot['close'].where(df_plot.index.isin(brs)),
                type='scatter',
                marker=breakout_marker,
                markersize=100,
                color=breakout_color,
            )
        )

    # 4. 绘图并保存
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    fig, _ = mpf.plot(
        df_plot,
        type="candle",
        style=style,
        volume=volume,
        addplot=addplots,
        title=title,
        figsize=figsize,
        returnfig=True,
        tight_layout=True,
        warn_too_much_data=len(df_plot)+1,
    )
    fig.savefig(out_path)
    plt.close(fig)
