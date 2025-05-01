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
        """
        position_size: 建仓时使用的资金比例（0~1），1.0=全仓，0.5=半仓...
        """
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
        entry_px = 0.0

        entries = set(entry_signals)
        exits   = set(exit_signals)

        for t, row in df.iterrows():
            # 先写入当前状态
            res.at[t,'cash']     = cash
            res.at[t,'position'] = qty

            # 1) 进场
            if t in entries and qty == 0:
                entry_px = row['open']
                invest   = cash * self.position_size
                qty      = invest / entry_px
                cash    -= invest
                res.at[t,'entry_price'] = entry_px

            # 2) 持仓期间：止损/止盈/跟踪止盈
            if qty > 0:
                exit_px = None
                if row['low'] <= entry_px * (1 - self.stop_loss):
                    exit_px = entry_px * (1 - self.stop_loss)
                elif row['high'] >= entry_px * (1 + self.take_profit):
                    exit_px = entry_px * (1 + self.take_profit)
                elif (
                    self.trailing_ma
                    and self.trailing_ma in df.columns
                    and row['close'] < row[self.trailing_ma]
                ):
                    exit_px = row['open']

                if exit_px is not None:
                    # **改动点：用 += 保留剩余 cash**
                    cash += qty * exit_px
                    qty   = 0.0
                    res.at[t,'exit_price'] = exit_px

            # 3) 兜底出场
            if t in exits and qty > 0:
                exit_px = row['open']
                cash   += qty * exit_px    # 同样用 +=
                qty     = 0.0
                res.at[t,'exit_price'] = exit_px

            # 刷新状态
            res.at[t,'cash']     = cash
            res.at[t,'position'] = qty

        # 4) 计算 pnl / equity / drawdown
        res['equity']     = res['cash'] + res['position'] * df['close']
        res['equity_max'] = res['equity'].cummax()
        res['drawdown']   = (res['equity'] - res['equity_max']) / res['equity_max']
        res['pnl']        = res['equity'].diff().fillna(0)

        return res[['cash','position','entry_price','exit_price','pnl','equity','drawdown']]
