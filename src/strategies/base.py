# src/strategies/base.py
import pandas as pd
from typing import List
import mplfinance as mpf

class StrategyBase:
    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError

    def get_signal_layers(self, df: pd.DataFrame) -> List:
        """
        返回一个或多个由 mpf.make_addplot(...) 生成的 addplot
        """
        raise NotImplementedError
