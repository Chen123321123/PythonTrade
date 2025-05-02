import pandas as pd
from typing import List, Optional

class Backtester:
    def __init__(
        self,
        init_cash: float,
        stop_loss: float,
        take_profit: float,
        trailing_ma: Optional[str] = None,
        position_size: float = 1.0
    ):
        self.init_cash     = init_cash
        self.stop_loss     = stop_loss
        self.take_profit   = take_profit
        self.trailing_ma   = trailing_ma
        self.position_size = position_size

    def run(
        self,
        df: pd.DataFrame,
        entry_signals: List[pd.Timestamp],
        exit_signals:  List[pd.Timestamp]
    ) -> pd.DataFrame:
        df = df.copy()
        res = pd.DataFrame(index=df.index)
        res['cash']        = 0.0
        res['position']    = 0.0
        res['entry_price'] = pd.NA
        res['exit_price']  = pd.NA

        cash = self.init_cash
        qty  = 0.0
        entry_px      = 0.0   # 下一根开盘买入价
        signal_price  = 0.0   # 信号 bar 收盘价
        pending_entry = False
        tp_reached    = False  # 是否已触及过利润目标

        entries = set(entry_signals)
        exits   = set(exit_signals)

        for t, row in df.iterrows():
            # 记录当前状态
            res.at[t,'cash']     = cash
            res.at[t,'position'] = qty

            # 1) 如果上一根 bar 有 pending_entry，则今根开盘买入
            if pending_entry:
                entry_px = row['open']
                invest   = cash * self.position_size
                qty      = invest / entry_px
                cash    -= invest
                res.at[t,'entry_price'] = entry_px
                pending_entry = False
                tp_reached    = False   # 重置止盈触发标志

            # 2) 本根 bar 检查新入场信号
            if t in entries and qty == 0:
                signal_price  = df.at[t, 'close']
                pending_entry = True

            # 3) 持仓期间：止损 or 止盈触发 or 触及 MA 止盈
            if qty > 0:
                # 3a) 止损标准
                sl_price = signal_price * (1 - self.stop_loss)
                if row['low'] <= sl_price:
                    exit_px = sl_price

                else:
                    exit_px = None
                    # 3b) 是否刚触及过止盈目标
                    if not tp_reached:
                        tp_price = signal_price * (1 + self.take_profit)
                        if row['high'] >= tp_price:
                            tp_reached = True

                    # 3c) 如果已触及过止盈目标，检查触及 MA
                    if tp_reached and self.trailing_ma in df.columns:
                        ma_val = row[self.trailing_ma]
                        if row['low'] <= ma_val:
                            exit_px = ma_val

                if exit_px is not None:
                    cash += qty * exit_px
                    qty   = 0.0
                    res.at[t,'exit_price'] = exit_px

            # 4) 外部强制退出信号：按开盘价平
            if t in exits and qty > 0:
                exit_px = row['open']
                cash   += qty * exit_px
                qty     = 0.0
                res.at[t,'exit_price'] = exit_px

            # 刷新状态
            res.at[t,'cash']     = cash
            res.at[t,'position'] = qty

        # 5) 计算 pnl / equity / drawdown
        res['equity']     = res['cash'] + res['position'] * df['close']
        res['equity_max'] = res['equity'].cummax()
        res['drawdown']   = (res['equity'] - res['equity_max']) / res['equity_max']
        res['pnl']        = res['equity'].diff().fillna(0)

        return res[['cash','position','entry_price','exit_price','pnl','equity','drawdown']]
