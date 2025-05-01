import pandas as pd
from typing import List, Tuple
import mplfinance as mpf

class BollingerNarrowStrategy:
    def __init__(self, window: int = 30, mult: float = 2, last_n: int = 200,
                 stop_loss: float = 0.05, take_profit: float = 0.10):
        self.window      = window
        self.mult        = mult
        self.last_n      = last_n
        self.stop_loss   = stop_loss
        self.take_profit = take_profit

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy().dropna()
        df['ma']   = df['close'].rolling(self.window).mean()
        df['mid']  = df['ma']
        df['std']  = df['close'].rolling(self.window).std()
        df['upper']= df['mid'] + self.mult * df['std']
        df['lower']= df['mid'] - self.mult * df['std']
        return df.dropna()

    def get_signal_layers(self, df: pd.DataFrame) -> Tuple[List[pd.Timestamp], List[pd.Timestamp]]:
        """
        返回两个列表：
         - entries：买入时间点
         - refs   ：参考点，这里我们也返回买入之后第一次突破上轨的时间（可当作“出场”参考）
        """
        prev = df.shift(1)
        entries, refs = [], []
        for t, row in df.iterrows():
            if prev.at[t, 'close'] < prev.at[t, 'upper'] and row['close'] > row['upper']:
                entries.append(t)
                refs.append(t)
        return entries, refs

    def get_exit_layers(self, df: pd.DataFrame) -> List[pd.Timestamp]:
        """
        根据止损/止盈规则，遍历标记真正出场时间点
        """
        prev = df.shift(1)
        exits = []
        in_pos = False
        entry_price = 0.0

        for t, row in df.iterrows():
            price = row['close']; ma = row['ma']

            # 开仓
            if not in_pos and prev.at[t, 'close'] < prev.at[t, 'upper'] and price > row['upper']:
                in_pos = True
                entry_price = price

            # 平仓：止损 or 止盈后跌破 MA
            elif in_pos:
                # 止损
                if row['low'] <= entry_price * (1 - self.stop_loss):
                    exits.append(t)
                    in_pos = False
                # 止盈（涨到目标后，价格跌破 ma）
                elif row['high'] >= entry_price * (1 + self.take_profit) and price < ma:
                    exits.append(t)
                    in_pos = False

        return exits

    def make_main_addplots(self, df: pd.DataFrame):
        return [
            mpf.make_addplot(df['upper'], color='grey',  width=0.8),
            mpf.make_addplot(df['mid'],   color='black', width=0.6),
            mpf.make_addplot(df['lower'], color='grey',  width=0.8),
        ]
