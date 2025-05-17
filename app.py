# app.py

import os
import sys
import requests
import ccxt

from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS

# 如果你的核心逻辑在 src/backend/core.py
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

@app.route("/results/<run_id>/<path:filename>", methods=["GET"])
def get_file(run_id, filename):
    base = request.args.get("base", "out")
    dirpath = os.path.join(base, run_id)
    return send_from_directory(dirpath, filename, as_attachment=False)

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
    coins = resp.json()  # 列表，每项里有 'symbol'

    # 2) 拼成大写 + "/USD"
    desired = [c["symbol"].upper() + "/USD" for c in coins]

    # 3) 取 Kraken 支持的交易对
    exchange = ccxt.kraken({"enableRateLimit": True})
    kraken_markets = set(exchange.load_markets().keys())

    # 4) 交集
    available = [s for s in desired if s in kraken_markets]
    return jsonify(available), 200

if __name__ == "__main__":
    # debug=True 会自动重载，方便开发
    app.run(host="0.0.0.0", port=5000, debug=True)
