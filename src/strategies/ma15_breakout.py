import pandas as pd
from typing import List, Tuple

class MA15BreakoutStrategy:
    def __init__(self, period: int = 15, last_n: int = 200,
                 stop_loss: float = 0.05, take_profit: float = 0.10):
        self.period      = period
        self.last_n      = last_n
        self.stop_loss   = stop_loss
        self.take_profit = take_profit

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().dropna()
        df['ma']       = df['close'].rolling(self.period).mean()
        df['above_ma'] = df['close'] > df['ma']
        return df.dropna()

    def get_signal_layers(self, df: pd.DataFrame) -> Tuple[List[pd.Timestamp], List[pd.Timestamp]]:
        prev = df.shift(1)
        entries, refs = [], []
        for t, row in df.iterrows():
            if not prev.at[t, 'above_ma'] and row['above_ma']:
                entries.append(t)
                refs.append(t)
        return entries, refs

    def get_exit_layers(self, df: pd.DataFrame) -> List[pd.Timestamp]:
        prev = df.shift(1)
        exits = []
        in_pos = False
        entry_price = 0.0

        for t, row in df.iterrows():
            price = row['close']; ma = row['ma']

            # 开仓
            if not in_pos and not prev.at[t, 'above_ma'] and row['above_ma']:
                in_pos = True
                entry_price = price

            # 平仓：止损 or 止盈后跌破 MA
            elif in_pos:
                if row['low'] <= entry_price * (1 - self.stop_loss):
                    exits.append(t)
                    in_pos = False
                elif row['high'] >= entry_price * (1 + self.take_profit) and price < ma:
                    exits.append(t)
                    in_pos = False

        return exits
