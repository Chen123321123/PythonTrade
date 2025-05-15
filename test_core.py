# test_core.py
import os
import sys

# 确保能 import src/backend
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

from backend.core import run_backtest_api  # 注意这里不加 src. 前缀

# 1) 准备一份示例参数
params = {
    "mode":          "backtest",              # 或 "plot"
    "symbols":       "BTC/USDT",              # 支持逗号分隔多个
    "timeframe":     "4h",
    "limit":         300,
    "last_n":        100,
    "strategy":      "bollinger_narrow",
    "children":      "",                      # follow_through 用
    "comb_mode":     "and",
    "window":        30,
    "mult":          2.0,
    "period":        15,
    "stop_loss":     0.05,
    "take_profit":   0.10,
    "trailing_ma":   "",
    "position_size": 1.0,
    "out_dir":       "out_test",              # 测试专用目录
}

# 2) 调用核心接口
result = run_backtest_api(params)

# 3) 打印返回值，检查结构
import pprint
pprint.pprint(result)
