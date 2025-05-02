# PythonTrade
# My Trading Bot

## 快速开始

```bash
git clone git@github.com:your-username/my_trading_bot.git
cd my_trading_bot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# 跑回测
python scripts/run_backtest.py

#提取数据
export PYTHONPATH="$PWD/src"
python scripts/fetch_csv.py \
  --symbols BTC/USDT,ETH/USDT \
  --timeframe 4h \
  --limit 300 \
  --out_dir data/csvs


  #布林轨策略（全仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 1000 \
  --last_n 300 \
  --strategy bollinger_narrow \
  --window 30 \
  --mult 2.0 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --position_size 1.0 \
  --out_dir charts/bollinger_narrow_backtest


  #布林轨策略（半仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 1000 \
  --last_n 300 \
  --strategy bollinger_narrow \
  --window 30 \
  --mult 2.0 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --position_size 0.5 \
  --out_dir charts/bollinger_narrow_backtest



  #MA15策略（全仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 300 \
  --last_n 300 \
  --strategy ma15_breakout \
  --period 15 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --trailing_ma ma \
  --position_size 1.0 \
  --out_dir charts/ma15_full

  #MA15策略（半仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 300 \
  --last_n 300 \
  --strategy ma15_breakout \
  --period 15 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --trailing_ma ma \
  --position_size 0.5 \
  --out_dir charts/ma15_full

  #结合策略（全仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 1000 \
  --last_n 300 \
  --strategy follow_through \
  --children bollinger_narrow,ma15_breakout \
  --comb_mode majority \
  --window 30 \
  --mult 2.0 \
  --period 15 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --position_size 1.0 \
  --trailing_ma ma \
  --out_dir charts/ft_backtest


  #结合策略（半仓）
  python scripts/run_backtest.py \
  --mode backtest \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 1000 \
  --last_n 300 \
  --strategy follow_through \
  --children bollinger_narrow,ma15_breakout \
  --comb_mode majority \
  --window 30 \
  --mult 2.0 \
  --period 15 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --position_size 0.5 \
  --trailing_ma ma \
  --out_dir charts/ft_backtest



    #画图
  python scripts/run_backtest.py \
  --mode plot \
  --symbols BTC/USDT \
  --timeframe 4h \
  --limit 300 \
  --strategy ma15_breakout \
  --out_dir charts/ma15 \
  --period 15 \
  --last_n 200 \
  --stop_loss 0.05 \
  --take_profit 0.10 \
  --trailing_ma ma






