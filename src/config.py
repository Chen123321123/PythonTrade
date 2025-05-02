# pythontrade/src/config.py

from pathlib import Path



# 回测时间
START_DATE = "2020-01-01"
END_DATE   = "2024-04-01"

# 项目根目录（src 的上一级）
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 本地数据目录，绝对指向项目根下的 data
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 交易所和 API（如果不拉私有接口，可留空）
EXCHANGE = "kraken"
API_KEY    = "<your_api_key>"
API_SECRET = "<your_api_secret>"

# 回测参数
INITIAL_CAPITAL = 100_000
COMMISSION_RATE = 0.001
