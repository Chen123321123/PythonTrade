# app.py

import os
import sys
import requests
import ccxt

from flask import Flask, request, jsonify, send_from_directory, render_template, abort
from flask_cors import CORS

# 如果核心逻辑在 src/backend/core.py
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from backend.core import run_backtest_api

app = Flask(__name__, template_folder="templates")
CORS(app)  # 允许跨域

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    params = request.get_json()
    result = run_backtest_api(params)
    return jsonify(result), 200

# 新增 alias 路径，指向同一逻辑
@app.route("/run_backtest", methods=["POST"])
def run_backtest():
    params = request.get_json()
    result = run_backtest_api(params)
    return jsonify(result), 200


@app.route("/results/<run_id>/<path:filename>", methods=["GET"])
def get_file(run_id, filename):
    project_root = os.path.dirname(os.path.abspath(__file__))
    out_root = os.path.join(project_root, "out")
    dirpath = os.path.join(out_root, run_id)
    fullpath = os.path.join(dirpath, filename)

    # 日志打印
    print(">>> SEND_FROM_DIRECTORY dirpath =", dirpath)
    print(">>>   fullpath =", fullpath)
    print(">>>   exists? ", os.path.exists(fullpath))

    if not os.path.isfile(fullpath):
        # 让 Flask 给出 404，并在日志里留下
        print(">>>   404 File Not Found!")
        abort(404)

    return send_from_directory(dirpath, filename, as_attachment=False)  

# 只允许 GET 查询 symbols
@app.route("/symbols", methods=["GET"])
def symbols():
    """
    返回 Kraken 交易所中，CoinGecko 市值前 100 的资产对应的 XXX/USD 交易对列表。
    """
    # 1) 调用 CoinGecko 接口取市值前100
    resp = requests.get(
        "https://api.coingecko.com/api/v3/coins/markets",
        params={
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 100,
            "page": 1
        },
        timeout=10,
    )
    resp.raise_for_status()
    coins = resp.json()

    # 2) 拼成大写 + "/USD"
    desired = [c["symbol"].upper() + "/USD" for c in coins]

    # 3) 取 Kraken 支持的交易对
    exchange = ccxt.kraken({"enableRateLimit": True})
    kraken_markets = set(exchange.load_markets().keys())

    # 4) 交集
    available = [s for s in desired if s in kraken_markets]
    return jsonify(available), 200

if __name__ == "__main__":
    # debug=True 仅用于本地开发，生产环境用 Gunicorn 启动
    app.run(host="0.0.0.0", port=5000, debug=True)
