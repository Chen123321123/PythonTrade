# src/strategies/follow_through.py
"""
CombinedFollowThroughStrategy:
等待所有/多数子策略曾发出买入意向后进场；
一旦任何子策略出场信号出现，立即平仓并重置意向。
"""

import pandas as pd
import importlib
import inspect
from typing import List, Dict, Any

class CombinedFollowThroughStrategy:
    def __init__(
        self,
        children: List[str],
        mode: str = "and",
        init_kwargs: Dict[str, Any] = {}
    ):
        assert mode in ("and","majority"), "mode must be 'and' or 'majority'"
        self.mode = mode
        self.strats = []
        for spec in children:
            mod_path, cls_name = spec.split(":")
            mod = importlib.import_module(mod_path)
            cls = getattr(mod, cls_name)
            sig = inspect.signature(cls.__init__)
            kw = {k: init_kwargs[k] for k in sig.parameters if k!="self" and k in init_kwargs}
            self.strats.append(cls(**kw))

    def compute(self, df: pd.DataFrame) -> pd.DataFrame:
        df2 = df.copy()
        n = len(self.strats)

        # 各策略原始信号列：+1 买，-1 卖/止损，0 无
        for idx, strat in enumerate(self.strats):
            sub = strat.compute(df)
            e_ts, _ = strat.get_signal_layers(sub)
            x_ts    = strat.get_exit_layers(sub)
            sig = pd.Series(0, index=df.index)
            sig.loc[e_ts] = 1
            sig.loc[x_ts] = -1
            df2[f"sig_{idx}"] = sig
            print(f">>> strat {idx} ({type(strat).__name__}) entry_ts:", e_ts[:5], "…")

        # 状态机：累计意向、进场、出场并重置
        done = {i: False for i in range(n)}
        entry_list, exit_list = [], []
        in_position = False

        for t, row in df2.iterrows():
            # 出场优先：任何子策略发 -1
            if any(row[f"sig_{i}"] == -1 for i in range(n)):
                if in_position:
                    exit_list.append(t)
                    in_position = False
                for i in range(n):
                    done[i] = False

            # 累计买入意向并检查进场
            if not in_position:
                for i in range(n):
                    if row[f"sig_{i}"] == 1:
                        done[i] = True
                if self.mode == "and":
                    if all(done.values()):
                        entry_list.append(t)
                        in_position = True
                else:  # majority
                    if sum(done.values()) >= (n//2 + 1):
                        entry_list.append(t)
                        in_position = True

        df2["entry"] = df2.index.isin(entry_list)
        df2["exit"]  = df2.index.isin(exit_list)
        return df2

    def get_signal_layers(self, df2: pd.DataFrame):
        return df2.index[df2["entry"]].tolist(), []

    def get_exit_layers(self, df2: pd.DataFrame):
        return df2.index[df2["exit"]].tolist()
