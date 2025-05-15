# app.py

import os
import sys

# ———————— Matplotlib 无头后端 ————————
import matplotlib
matplotlib.use("Agg")

# ———————— Flask 相关 ————————
from flask import Flask, request, jsonify, send_from_directory, render_template

# 将 src 加入 Python 模块搜索路径
sys.path.insert(0, os.path.join(os.getcwd(), "src"))
from backend.core import run_backtest_api

app = Flask(__name__, template_folder="templates")

@app.route("/", methods=["GET"])
def index():
    """
    渲染前端页面，提供表单让用户提交回测参数并查看结果图片。
    """
    return render_template("index.html")

@app.route("/run", methods=["POST"])
def run():
    """
    启动回测／信号绘制任务。
    接收 JSON，调用 run_backtest_api，返回 run_id 和 base（输出根目录）。
    """
    params = request.get_json()
    result = run_backtest_api(params)
    return jsonify({
        "run_id": result["run_id"],
        "base":   params["out_dir"]
    }), 202

@app.route("/results/<run_id>/<path:filename>", methods=["GET"])
def get_file(run_id, filename):
    """
    下载指定任务的产出文件。
    URL 参数：
      run_id   - /run 返回的任务 ID
      filename - 文件名，如 BTC_USDT_signals.png
    Query 参数：
      base - out_dir 根目录（默认为 "out"）
    """
    base = request.args.get("base", "out")
    dirpath = os.path.join(base, run_id)
    return send_from_directory(dirpath, filename, as_attachment=False)

if __name__ == "__main__":
    # 开发模式启动；生产环境请使用 Gunicorn/Uvicorn 等 WSGI/ASGI 服务器
    app.run(host="0.0.0.0", port=5000)
